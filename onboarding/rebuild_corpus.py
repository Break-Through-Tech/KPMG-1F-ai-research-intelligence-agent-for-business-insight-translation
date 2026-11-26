"""Retrieve versioned arXiv HTML and test reconstruction of the evaluated index."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import time
from urllib.request import Request, urlopen

from setup import ROOT, SetupError, sha256, verify

SOURCES = ROOT / 'onboarding/demo-100-sources.json'
MAX_HTML = 5_000_000


def records():
    return json.loads(SOURCES.read_bytes())['papers']


def retrieve_sources(cache, *, papers=None):
    cache.mkdir(parents=True, exist_ok=True)
    papers = records() if papers is None else papers
    report = []
    for position, paper in enumerate(papers, 1):
        ident, pin = paper['id'], paper['html_sha256']
        if not re.fullmatch(r'\d{4}\.\d{4,5}v\d+', ident):
            raise SetupError('Invalid pinned arXiv version.')
        path = cache / (ident + '.html')
        result = {'id': ident, 'expected_sha256': pin}
        try:
            if path.is_file() and sha256(path) == pin:
                result.update(status='exact', actual_sha256=pin)
            else:
                print(f'Checking versioned arXiv source {position}/{len(papers)}: {ident}', flush=True)
                url = f'https://arxiv.org/html/{ident}'
                request = Request(url, headers={'User-Agent': 'KPMG-research-onboarding/1.0'})
                with urlopen(request, timeout=20) as response:
                    if response.geturl() != url or response.headers.get_content_type() != 'text/html':
                        raise ValueError('arXiv returned a different resource or non-HTML content')
                    raw = response.read(MAX_HTML + 1)
                if len(raw) > MAX_HTML:
                    raise ValueError('HTML exceeds original reader limit')
                actual = hashlib.sha256(raw).hexdigest()
                result.update(status='exact' if actual == pin else 'changed', actual_sha256=actual)
                if actual == pin:
                    path.write_bytes(raw)
                time.sleep(1)
        except (OSError, ValueError) as error:
            result.update(status='unavailable', reason=str(error))
        report.append(result)
    path = cache.parent / 'source-verification.json'
    path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return report


def encode_parents(parents):
    return '\r\n'.join(json.dumps(p, ensure_ascii=False, allow_nan=False) for p in parents).encode()


def rebuild(workspace):
    sys.path.insert(0, str(ROOT))
    from src.experimental.arxiv_fallback import html_passages
    from src.experimental.html_evidence import VERSION
    from src.experimental.build_bundle import build_bundle
    from sentence_transformers import SentenceTransformer

    parents, reports = [], []
    papers = records()
    for paper in papers:
        ident = paper['id']
        if set(paper['extractors']) - {'legacy-prose-chunker', VERSION}:
            reports.append({'id': ident, 'status': 'extractor unavailable',
                            'required_extractors': paper['extractors']})
            continue
        path = workspace / 'arxiv-html' / (ident + '.html')
        if not path.is_file() or sha256(path) != paper['html_sha256']:
            reports.append({'id': ident, 'status': 'source missing or changed'})
            continue
        try:
            extracted = html_passages(path.read_bytes(), {'arxiv_id': ident, 'title': paper['title']})
            actual = hashlib.sha256(encode_parents(extracted)).hexdigest()
            okay = actual == paper['parents_sha256'] and len(extracted) == paper['parents']
            reports.append({'id': ident, 'status': 'exact' if okay else 'extraction changed',
                            'expected_sha256': paper['parents_sha256'], 'actual_sha256': actual,
                            'expected_rows': paper['parents'], 'actual_rows': len(extracted)})
            if okay:
                parents.extend(extracted)
        except (ValueError, TypeError, KeyError) as error:
            reports.append({'id': ident, 'status': 'extraction failed', 'reason': str(error)})
    (workspace / 'extraction-verification.json').write_text(json.dumps(reports, indent=2), encoding='utf-8')
    errors = [r for r in reports if r['status'] != 'exact']
    if errors:
        raise SetupError(f'{len(errors)} paper extractions differ or are unavailable. '
                         'See extraction-verification.json. The evaluated index was not replaced.')
    assets = workspace / 'assets'
    spec = json.loads((ROOT / 'onboarding/assets.json').read_bytes())
    evaluated = json.loads((ROOT / 'onboarding/runtime-metadata/demo-100/manifest.json').read_bytes())
    if hashlib.sha256(encode_parents(parents)).hexdigest() != evaluated['artifact_sha256']['parents.jsonl']:
        raise SetupError('Reassembled parents differ from the evaluated index.')
    outroot = ROOT / 'data/processed'
    outroot.mkdir(parents=True, exist_ok=True)
    model = SentenceTransformer(str(assets / 'models/encoder'), local_files_only=True, device='cpu')
    with tempfile.TemporaryDirectory(prefix='onboarding-rebuild-', dir=outroot) as tmp:
        candidate = Path(tmp) / 'bundle'
        build_bundle(parents, candidate, model, strategy='token224_parent')
        (candidate / 'parents.jsonl').write_bytes(encode_parents(parents))
        report = {}
        for name, expected in evaluated['artifact_sha256'].items():
            report[name] = {'expected_sha256': expected, 'actual_sha256': sha256(candidate / name)}
        (workspace / 'index-verification.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        if any(v['actual_sha256'] != v['expected_sha256'] for v in report.values()):
            raise SetupError('Rebuilt index bytes differ. See index-verification.json. Nothing was promoted.')
        for name in report:
            target = assets / 'demo-100' / name
            verify(candidate / name, spec['files']['demo-100/' + name])
            if target.exists():
                verify(target, spec['files']['demo-100/' + name])
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(candidate / name, target)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, default=ROOT / '.kpmg-onboarding')
    parser.add_argument('--check-sources', action='store_true')
    parser.add_argument('--limit', type=int, help='Diagnostic subset, only with --check-sources')
    args = parser.parse_args()
    if args.limit is not None and not args.check_sources:
        parser.error('--limit applies only to --check-sources.')
    if args.check_sources:
        status = retrieve_sources(args.workspace / 'arxiv-html', papers=records()[:args.limit])
        counts = {state: sum(row['status'] == state for row in status)
                  for state in ('exact', 'changed', 'unavailable')}
        print(counts)
        if counts['changed'] or counts['unavailable']:
            raise SetupError('Source differences recorded in source-verification.json.')
    else:
        rebuild(args.workspace)


if __name__ == '__main__':
    try:
        main()
    except ModuleNotFoundError as error:
        sys.exit(f'Reconstruction dependency missing: {error.name}. Use the recorded ingestion environment.')
    except (SetupError, OSError) as error:
        sys.exit(f'Reconstruction error: {error}')
