"""Bounded arXiv discovery/replay into a SEPARATE candidate dataset.

No ingestion, persistent vector-index writes, or commits. Date windows describe
new submissions, not all revisions to old papers. Dates are UTC, until exclusive.
"""
import argparse
import csv
from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
import io
import json
from pathlib import Path
import re
import time
import xml.etree.ElementTree as ET

ATOM = '{http://www.w3.org/2005/Atom}'
ARXIV = '{http://arxiv.org/schemas/atom}'
OPENSEARCH = '{http://a9.com/-/spec/opensearch/1.1/}'
API = 'https://export.arxiv.org/api/query'
FIELDS = ['arxiv_id', 'title', 'authors', 'abstract', 'categories', 'published', 'updated', 'pdf_url']
ID = re.compile(r'^(?P<base>\d{4}\.\d{4,5}|[a-z][a-z.\-]+/\d{7})(?:v(?P<version>[1-9]\d*))?$')


def identity(value):
    value = value.strip()
    match = ID.fullmatch(value)
    if not match:
        raise ValueError(f'Invalid arXiv ID: {value!r}')
    return match['base'], int(match['version']) if match['version'] else None


def parse_feed(body):
    root = ET.fromstring(body)
    error = root.find(ATOM+'entry/'+ATOM+'id')
    if error is not None and '/errors' in (error.text or ''):
        raise ValueError('arXiv returned an API error entry')
    records = []
    for entry in root.findall(ATOM+'entry'):
        ident = entry.findtext(ATOM+'id', '').split('/abs/')[-1]
        base, version = identity(ident)
        if version is None:
            raise ValueError('API did not resolve a versioned paper')
        row = {'arxiv_id': ident, 'base_id': base, 'version': version,
               'title': ' '.join(entry.findtext(ATOM+'title', '').split()),
               'abstract': ' '.join(entry.findtext(ATOM+'summary', '').split()),
               'authors': ', '.join(a.findtext(ATOM+'name', '') for a in entry.findall(ATOM+'author')),
               'categories': ', '.join(c.attrib['term'] for c in entry.findall(ATOM+'category')),
               'published': entry.findtext(ATOM+'published', ''),
               'updated': entry.findtext(ATOM+'updated', ''),
               'pdf_url': 'https://arxiv.org/pdf/'+ident}
        if not row['title'] or not row['abstract'] or not row['published']:
            raise ValueError('API record missing required metadata')
        records.append(row)
    total_text = root.findtext(OPENSEARCH+'totalResults')
    if total_text is None:
        raise ValueError('API feed missing totalResults; cannot infer completeness')
    return records, int(total_text)


def atomic_write(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name+'.tmp')
    temp.write_text(text, encoding='utf-8')
    temp.replace(path)


class HTTP:
    def __init__(self, *, delay=3.1, attempts=3):
        import requests
        self.session = requests.Session()
        self.session.headers['User-Agent'] = 'KPMG-1F-local-collector/0.1 (bounded research prototype)'
        self.delay, self.attempts, self.last_request = delay, attempts, 0.0

    def get(self, url, *, params=None):
        import requests
        for attempt in range(self.attempts):
            time.sleep(max(0, self.delay - (time.monotonic()-self.last_request)))
            self.last_request = time.monotonic()
            try:
                r = self.session.get(url, params=params, timeout=30)
                if r.status_code == 429 or r.status_code >= 500:
                    if attempt+1 < self.attempts:
                        # Bound waits; preserve checkpoint on repeated throttle.
                        time.sleep(min(10, self.delay * 2**attempt))
                        continue
                r.raise_for_status()
                return r.content
            except requests.RequestException as exc:
                if (getattr(exc, 'response', None) is not None
                        and 400 <= exc.response.status_code < 500
                        and exc.response.status_code != 429):
                    raise
                if attempt+1 == self.attempts:
                    raise
        raise RuntimeError('Request attempts exhausted')


def specification(args):
    if args.ids:
        for ident in args.ids:
            identity(ident)
        if args.since or args.until or args.query or args.category or args.keyword:
            raise ValueError('Exact-ID replay cannot also set discovery filters')
        if len(set(args.ids)) > args.max_results:
            raise ValueError('Exact replay IDs exceed max-results')
        return {'ids': sorted(set(args.ids)), 'policy': 'exact-ID replay; unversioned IDs resolve latest'}
    if not args.since or not args.until:
        raise ValueError('Discovery requires --since and --until (UTC dates, exclusive until)')
    since, until = date.fromisoformat(args.since), date.fromisoformat(args.until)
    if since >= until:
        raise ValueError('since must precede until')
    terms = []
    if args.category:
        if not re.fullmatch(r'[A-Za-z][A-Za-z0-9.\-]*', args.category):
            raise ValueError('Invalid category')
        terms.append('cat:'+args.category)
    if args.query:
        terms.append('('+args.query+')')
    last = datetime.combine(until, datetime.min.time()) - timedelta(minutes=1)
    terms.append(f'submittedDate:[{since:%Y%m%d}0000 TO {last:%Y%m%d%H%M}]')
    return {'search_query': ' AND '.join(terms), 'since': args.since, 'until': args.until,
            'keywords': sorted(set(k.lower() for k in args.keyword)),
            'policy': 'new submissions only; revisions of older papers need separate exact replay'}


def collect(args, *, http=None):
    if any(isinstance(n, bool) or not isinstance(n, int) or n < 1
           for n in (args.max_results, args.page_size)) or args.page_size > 100:
        raise ValueError('Positive limits required; page-size must be <= 100')
    spec = specification(args)
    fingerprint = sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()
    out = Path(args.output)
    state_path = out/'checkpoint.json'
    state = json.loads(state_path.read_text()) if state_path.exists() else {
        'schema_version': 1, 'specification': spec, 'fingerprint': fingerprint,
        'next_start': 0, 'exhausted': False, 'records': {}}
    if state.get('fingerprint') != fingerprint:
        raise ValueError('Output checkpoint belongs to different filters; use a new directory')
    http = http or HTTP()
    records = state['records']
    report = {'schema_version': 1, 'specification': spec, 'fingerprint': fingerprint,
              'created_at': datetime.now(timezone.utc).isoformat(), 'dry_run': args.dry_run,
              'discovered': 0, 'matched': 0, 'existing': 0, 'new': 0, 'new_versions': 0,
              'downloads_completed': 0, 'downloads_failed': 0, 'downloads_existing': 0,
              'would_download': 0, 'errors': [], 'coverage_status': 'unknown',
              'ingestion_status': 'not_attempted', 'next_start': state['next_start']}

    def save():
        if args.dry_run:
            return
        ordered = [records[k] for k in sorted(records)]
        atomic_write(state_path, json.dumps(state, indent=2)+'\n')
        atomic_write(out/'metadata.jsonl', ''.join(json.dumps({k:r[k] for k in FIELDS})+'\n' for r in ordered))
        text = io.StringIO()
        writer = csv.DictWriter(text, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows({k:r[k] for k in FIELDS} for r in ordered)
        atomic_write(out/'metadata.csv', text.getvalue())
        atomic_write(out/'manifest.json', json.dumps({'fingerprint':fingerprint,
            'specification':spec, 'papers':ordered, 'corpus_role':'candidate_only',
            'metadata_csv_sha256':sha256(text.getvalue().encode()).hexdigest()},indent=2)+'\n')

    acquisitions = 0
    def acquire(row):
        nonlocal acquisitions
        if not args.download:
            return
        if args.dry_run:
            report['would_download'] += 1
            return
        path = out/'pdfs'/(row['arxiv_id'].replace('/','_')+'.pdf')
        if path.exists():
            data = path.read_bytes()
            if data.startswith(b'%PDF-') and sha256(data).hexdigest() == row.get('pdf_sha256'):
                report['downloads_existing'] += 1
                return
        if acquisitions >= args.max_results:
            report['downloads_deferred'] = report.get('downloads_deferred', 0) + 1
            return
        acquisitions += 1
        try:
            data = http.get(row['pdf_url'])
            if not data.startswith(b'%PDF-') or b'%%EOF' not in data[-4096:]:
                raise ValueError('Download lacks PDF header or EOF marker')
            path.parent.mkdir(parents=True, exist_ok=True)
            temp = path.with_suffix('.pdf.part')
            temp.write_bytes(data)
            temp.replace(path)
            row.update(download_status='complete', pdf_sha256=sha256(data).hexdigest(),
                       pdf_path=str(path.relative_to(out)))
            row.pop('download_error', None)
            report['downloads_completed'] += 1
        except Exception as exc:
            row.update(download_status='failed',download_error=type(exc).__name__)
            report['downloads_failed'] += 1
        save()

    # Retry known failures/missing/corrupted files even after discovery exhausted.
    for row in list(records.values()):
        acquire(row)
    try:
        while not state['exhausted'] and report['discovered'] < args.max_results:
            size = min(args.page_size, args.max_results-report['discovered'])
            if args.ids:
                params = {'id_list':','.join(spec['ids']), 'max_results':len(spec['ids'])}
            else:
                params = {'search_query':spec['search_query'],'start':state['next_start'],
                          'max_results':size,'sortBy':'submittedDate','sortOrder':'ascending'}
            batch, total = parse_feed(http.get(API, params=params))
            if len(batch) > (len(spec['ids']) if args.ids else size):
                raise ValueError('API exceeded requested page size')
            report['total_reported'] = total
            if not batch and state['next_start'] < total:
                raise ValueError('Empty API page before reported total; checkpoint not advanced')
            if args.ids:
                # Missing IDs are failures, never silently marked complete.
                for requested in spec['ids']:
                    base, version = identity(requested)
                    if not any(r['base_id']==base and (version is None or r['version']==version) for r in batch):
                        raise ValueError('Exact replay did not return every requested ID/version')
                if any(not any(identity(i)[0]==r['base_id'] and
                    (identity(i)[1] is None or identity(i)[1]==r['version']) for i in spec['ids']) for r in batch):
                    raise ValueError('Exact replay returned an unrequested paper')
            for row in batch:
                report['discovered'] += 1
                keywords = spec.get('keywords', [])
                if keywords and not all(k in row['abstract'].lower() for k in keywords):
                    continue
                report['matched'] += 1
                ident = row['arxiv_id']
                if ident in records:
                    report['existing'] += 1
                    continue  # Keep scanning; never break at a seen ID.
                versions = [r['version'] for r in records.values() if r['base_id']==row['base_id']]
                if versions and row['version'] > max(versions):
                    report['new_versions'] += 1
                report['new'] += 1
                row['download_status'] = 'not_requested'
                records[ident] = row
                save()  # An interrupted page is safely replayed.
                acquire(row)
            state['next_start'] += len(batch)
            state['exhausted'] = bool(args.ids) or state['next_start'] >= total
            save()
            if not batch:
                break
        report['coverage_status'] = 'window_exhausted' if state['exhausted'] else 'truncated_resumable'
    except Exception as exc:
        report['errors'].append({'type':type(exc).__name__, 'message':str(exc)})
        report['coverage_status'] = 'failed_resumable'
        save()
    report['next_start'] = state['next_start']
    report['candidate_records'] = len(records)
    report['pending_download_failures'] = sum(r['download_status']=='failed' for r in records.values())
    if not args.dry_run:
        atomic_write(out/'report.json',json.dumps(report,indent=2)+'\n')
    return report


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ids', nargs='+', default=[])
    p.add_argument('--category')
    p.add_argument('--query')
    p.add_argument('--keyword', action='append', default=[])
    p.add_argument('--since')
    p.add_argument('--until')
    p.add_argument('--max-results',type=int,default=25)
    p.add_argument('--page-size',type=int,default=25)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--dry-run',action='store_true')
    p.add_argument('--download',action='store_true')
    args = p.parse_args(argv)
    try:
        report = collect(args)
    except ValueError as exc:
        p.error(str(exc))
    print(json.dumps(report,indent=2))
    return int(bool(report['errors'] or report['pending_download_failures']))


if __name__ == '__main__':
    raise SystemExit(main())
