"""Offline, source-backed bibliography/citation graph. Never crawls or indexes.

Edges record citation syntax, not support, endorsement or intellectual influence.
Identity resolution uses explicit arXiv metadata only, never title similarity.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import tempfile

import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.bibdatabase import BibDataString, BibDataStringExpression

from .tex_assets import asset_members, literal_preamble
from .tex_lexical import structural
from .tex_source import MAX_ARCHIVE, _name, read_source, source_blocks, source_url

MAX_RECORDS = 10000
MAX_PAPERS = 100
MAX_GRAPH_BYTES = 100 * 1024 * 1024
MAX_SITES = 20000
ARXIV = r'(?:\d{4}\.\d{4,5}|[a-z-]+(?:\.[A-Z]{2})?/\d{7})(?:v\d+)?'
CITE = re.compile(r'\\((?:[Cc]ite[a-zA-Z]*|[Tt]extcites?|[Pp]arencites?|[Aa]utocites?|[Ff]ootcites?|[Ss]martcites?|[Ss]upercites?|nocite))\*?(?:\s*\([^)]*\))*(?:\s*\[[^\]]*\])*\s*\{([^{}]+)\}')
DECLARATION = re.compile(r'\\(?:bibliography|addbibresource)(?:\s*\[[^\]]*\])?\s*\{([^{}]+)\}')
BIBITEM = re.compile(r'\\bibitem(?:\s*\[[^\]]*\])?\s*\{([^{}]+)\}')


MULTICITES = {'cites', 'textcites', 'parencites', 'autocites', 'footcites', 'smartcites', 'supercites'}
NEXT_CITE_GROUP = re.compile(r'(?:\s*\[[^\]]*\])*\s*\{([^{}]+)\}')


def citation_sites(code):
    for match in CITE.finditer(code):
        yield match[1], match[2], match.start()
        if match[1].lower() in MULTICITES:
            cursor = match.end()
            while group := NEXT_CITE_GROUP.match(code, cursor):
                yield match[1], group[1], match.start()
                cursor = group.end()


def entry_locations(text):
    """Locate top-level entries, never entry-shaped text inside field values."""
    locations = defaultdict(list)
    opener = re.compile(r'@([a-zA-Z]+)\s*([({])')
    cursor = 0
    while match := opener.search(text, cursor):
        start, index = match.start(), match.end()
        header = re.match(r'\s*([^,\s]+)\s*,', text[index:])
        if header and match[1].lower() not in {'comment', 'string', 'preamble'}:
            locations[header[1]].append(start)
        brace_depth, quote, escaped = (1 if match[2] == '{' else 0), False, False
        while index < len(text):
            char = text[index]
            index += 1
            if escaped:
                escaped = False
                continue
            if char == '\\':
                escaped = True
            elif char == '"' and brace_depth == (1 if match[2] == '{' else 0):
                quote = not quote
            elif not quote:
                if char == '{':
                    brace_depth += 1
                elif char == '}':
                    brace_depth -= 1
                    if match[2] == '{' and brace_depth == 0:
                        break
                elif char == ')' and match[2] == '(' and brace_depth == 0:
                    break
        cursor = index
    return locations


def base_id(aid):
    if '/' in aid:
        category, number = aid.split('/', 1)
        parts = category.split('.', 1)
        aid = parts[0].lower() + ('.' + parts[1].upper() if len(parts) > 1 else '') + '/' + number
    source_url(aid)  # Shared validation, including legacy identifiers.
    return re.sub(r'v\d+$', '', aid).lower()


def arxiv_identifiers(fields):
    found = set()
    for field, value in fields.items():
        if field.lower() not in {'url', 'doi', 'eprint', 'note', 'howpublished', 'raw'}:
            continue
        found.update(re.findall(r'(?:https?://(?:www\.)?arxiv\.org/(?:abs|pdf)/|arxiv\s*:\s*|10\.48550/arxiv\.)('
                                + ARXIV + r')(?:\.pdf)?(?!\w|\.\d)', value, re.I))
    eprint = fields.get('eprint', '').strip()
    prefix = fields.get('archiveprefix', fields.get('eprinttype', '')).lower()
    if prefix in ('', 'arxiv') and re.fullmatch(ARXIV, eprint):
        found.add(eprint)
    return sorted(found)


def bounded_string(value, database, seen=(), budget=None):
    """Resolve only bounded acyclic string expressions, never recursive get_value."""
    budget = [0, 0] if budget is None else budget
    budget[0] += 1
    if len(seen) > 32 or budget[0] > 10000:
        raise ValueError('Bibliography string expansion limit')
    if isinstance(value, str):
        budget[1] += len(value)
        if budget[1] > 1024 * 1024:
            raise ValueError('Bibliography string byte limit')
        return value
    if isinstance(value, BibDataString):
        if value.name in seen:
            raise ValueError('Cyclic bibliography string')
        return bounded_string(database.strings[value.name], database, (*seen, value.name), budget)
    if isinstance(value, BibDataStringExpression):
        return ''.join(bounded_string(part, database, seen, budget) for part in value.expr)
    raise ValueError('Unsupported bibliography string expression')


def _bib_entries(name, text):
    strings = re.findall(r'@string\s*[({]\s*([\w-]+)\s*=', text, re.I)
    duplicates = sorted(k for k, count in Counter(v.lower() for v in strings).items() if count > 1)
    parser = BibTexParser(common_strings=True)
    parser.ignore_nonstandard_types = False
    parser.interpolate_strings = False
    database = bibtexparser.loads(text, parser=parser)
    # bibtexparser's partial mode silently accepts a prefix of a broken file.
    # Unparsed comments containing entry syntax therefore fail this asset.
    if any(re.search(r'@\s*[a-zA-Z]+\s*[({]', c) for c in database.comments):
        raise ValueError('Unparsed bibliography entry syntax')
    entries = []
    locations = entry_locations(text)
    occurrences = Counter()
    for entry in database.entries:
        key = entry['ID']
        fields, unresolved = {}, []
        for field, value in entry.items():
            if not isinstance(value, str):
                if duplicates:
                    # Never silently choose among repeated string declarations.
                    unresolved.append(field)
                    fields[field] = str(value)
                    continue
                try:
                    value = bounded_string(value, database)
                except (KeyError, AttributeError, ValueError):
                    unresolved.append(field)
                    value = str(value)
            fields[field] = value
        position = locations[key][occurrences[key]] if occurrences[key] < len(locations[key]) else None
        occurrences[key] += 1
        entries.append(dict(key=key, fields=fields, source_file=name,
                            line=1 + text[:position].count('\n') if position is not None else None,
                            format='bib', unresolved_string_fields=unresolved, duplicate_string_definitions=duplicates))
    return entries


def _inline_entries(name, text, first_line=1, format='inline_bibitem'):
    code = structural(text)[1]
    matches = list(BIBITEM.finditer(code))
    result = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        stop = code.find(r'\end{thebibliography}', match.end(), end)
        if stop >= 0:
            end = stop
        result.append(dict(key=match[1], fields={'raw': text[match.end():end].strip()},
                           source_file=name, line=first_line + text[:match.start()].count('\n'),
                           format=format, unresolved_string_fields=[]))
    return result


def bibliography(data):
    """Resolve declared .bib paths; root-matched BBL fallback stays provisional."""
    blocks = source_blocks(data)
    files, manifest = read_source(data, with_manifest=True)
    roots = [name for name, text in files.items() if r'\begin{document}' in structural(text)[1]]
    if manifest:
        declared = [s['filename'] for s in manifest['sources'] if s.get('usage') == 'toplevel']
        if declared:
            roots = declared
    root = _name(roots[0])
    root_dir = PurePosixPath(root).parent
    names, _ = asset_members(data)
    selected, missing, ambiguous, sites, entries = set(), [], [], defaultdict(list), []
    site_count = 0
    # BibLaTeX commonly declares resources before begin{document}. These
    # declarations are inspected separately; preamble citations are not edges.
    preamble = literal_preamble(files[root])
    declarations = [(root, preamble)]
    for name, line, text in blocks:
        code = structural(text)[1]
        for command, keys, position in citation_sites(code):
            for key in keys.split(','):
                key = key.strip()
                if not key:
                    continue
                sites[key].append(dict(source_file=name, line=line + text[:position].count('\n'),
                                       command=command))
                site_count += 1
                if site_count > MAX_SITES:
                    raise ValueError('Citation site limit exceeded')
        declarations.append((name, code))
        entries.extend(_inline_entries(name, text, line))
    for name, code in declarations:
        for match in DECLARATION.finditer(code):
            for reference in match[1].split(','):
                try:
                    reference = _name(reference.strip())
                    if '\\' in reference or not reference:
                        raise ValueError('Dynamic bibliography reference')
                    if not reference.endswith('.bib'):
                        reference += '.bib'
                    candidates = {_name(str(base / reference))
                                  for base in (root_dir, PurePosixPath(name).parent)}.intersection(names)
                    if len(candidates) == 1:
                        selected.update(candidates)
                    elif candidates:
                        ambiguous.append(reference)
                    else:
                        missing.append(reference)
                except ValueError:
                    missing.append(match[1])
    bbl = str(PurePosixPath(root).with_suffix('.bbl'))
    # Do not select unrelated bundled generated outputs. Even root filename
    # correspondence does not prove build/revision correspondence.
    fallback = [bbl] if missing and not ambiguous and bbl in names else []
    _, assets = asset_members(data, selected | set(fallback))
    errors = []
    for name in sorted(selected):
        try:
            entries.extend(_bib_entries(name, assets[name].decode('utf-8-sig')))
        except (ValueError, UnicodeError) as error:
            errors.append(dict(source_file=name, error=str(error)))
    for name in fallback:
        try:
            entries.extend(_inline_entries(name, assets[name].decode('utf-8-sig'),
                                           format='root_bbl_candidate'))
        except (ValueError, UnicodeError) as error:
            errors.append(dict(source_file=name, error=str(error)))
    if len(entries) > MAX_RECORDS:
        raise ValueError('Bibliography record limit exceeded')
    return dict(entries=entries, citation_sites=dict(sites), selected_bib=sorted(selected),
                missing_declared_bib=missing, ambiguous_declared_bib=ambiguous,
                bbl_candidates=fallback, parse_errors=errors)


def build_graph(papers):
    """papers: [{arxiv_id, title, source_bytes}]. Returns JSON-serializable data."""
    if not papers or len(papers) > MAX_PAPERS:
        raise ValueError('Graph requires 1..100 papers')
    if sum(len(p['source_bytes']) for p in papers) > MAX_GRAPH_BYTES:
        raise ValueError('Graph input byte limit exceeded')
    nodes, edges, receipts, versions = {}, [], [], set()
    for paper in papers:
        aid, data = paper['arxiv_id'], paper['source_bytes']
        source = 'arxiv:' + base_id(aid)
        if aid in versions:
            raise ValueError('Duplicate source version')
        versions.add(aid)
        digest = hashlib.sha256(data).hexdigest()
        layer = bibliography(data)
        counts = Counter(entry['key'] for entry in layer['entries'])
        sites = layer['citation_sites']
        nodes.setdefault(source, dict(id=source, kind='arxiv_metadata_identity', arxiv_id=base_id(aid)))
        nodes[source].update(is_source=True, title=paper.get('title', aid))
        matched = set()
        for index, entry in enumerate(layer['entries']):
            key = entry['key']
            matched.add(key)
            identifiers = arxiv_identifiers(entry['fields'])
            bases = sorted({base_id(i) for i in identifiers})
            uncertain = (len(bases) != 1 or counts[key] != 1 or
                         entry['format'] == 'root_bbl_candidate' or
                         bool(entry['unresolved_string_fields']))
            target = ('reference:' + aid + ':' + str(index) if uncertain else 'arxiv:' + bases[0])
            node = dict(id=target, kind='bibliography_reference', fields=entry['fields'])
            if not uncertain:
                node = dict(id=target, kind='arxiv_metadata_identity', arxiv_id=bases[0])
            nodes.setdefault(target, node)
            cited = any(s['command'] != 'nocite' for s in sites.get(key, []))
            edges.append(dict(source=source, target=target, type='cites' if cited else 'bibliography_only',
                source_version=aid, source_sha256=digest, citation_key=key,
                citation_sites=sites.get(key, []), bibliography_file=entry['source_file'],
                bibliography_line=entry['line'], format=entry['format'], fields=entry['fields'],
                arxiv_ids=identifiers, identity_status='unresolved_or_provisional' if uncertain else 'explicit_metadata_unverified',
                unresolved_string_fields=entry['unresolved_string_fields'],
                duplicate_string_definitions=entry.get('duplicate_string_definitions', [])))
        # Unresolved keys remain inspectable, never case-folded or title-guessed.
        receipts.append(dict(arxiv_id=aid, source_sha256=digest,
            unresolved_keys=sorted(set(sites) - matched - {'*'}),
            duplicate_keys=sorted(k for k, count in counts.items() if count > 1),
            **{k:v for k,v in layer.items() if k not in ('entries', 'citation_sites')}))
    return dict(schema_version='citation-graph-v1', automatic_expansion=False,
                semantics='explicit citation syntax only; not support or endorsement; identities not remotely verified',
                nodes=list(nodes.values()), edges=edges, papers=receipts)


def expansion_candidates(graph, limit=10):
    """Offline hints only. Relevance and exact-version acquisition are not done."""
    if isinstance(limit, bool) or not isinstance(limit, int) or not 0 <= limit <= 10:
        raise ValueError('Candidate limit must be 0..10')
    sources = {n['id'] for n in graph['nodes'] if n.get('is_source')}
    citing = defaultdict(set)
    for edge in graph['edges']:
        if (edge['type'] == 'cites' and edge['identity_status'] == 'explicit_metadata_unverified'
                and edge['target'].startswith('arxiv:') and edge['target'] not in sources):
            citing[edge['target']].add(edge['source'])
    ranked = sorted(citing, key=lambda key: (-len(citing[key]), key))[:limit]
    return dict(enabled=False, max_hops=1, candidates=[dict(arxiv_id=key[6:],
        citing_papers=len(citing[key]), status='candidate_only_not_downloaded') for key in ranked])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', action='append', required=True, metavar='ARXIV_ID=PATH')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    papers, total = [], 0
    if len(args.source) > MAX_PAPERS:
        parser.error('Too many graph sources')
    for item in args.source:
        aid, separator, path = item.partition('=')
        if not separator:
            parser.error('--source must be ARXIV_ID=PATH')
        source_url(aid)
        with Path(path).open('rb') as stream:
            data = stream.read(MAX_ARCHIVE + 1)
        total += len(data)
        if total > MAX_GRAPH_BYTES:
            parser.error('Graph input byte limit exceeded')
        papers.append(dict(arxiv_id=aid, source_bytes=data))
    graph = build_graph(papers)
    graph['expansion_candidates'] = expansion_candidates(graph)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=args.output.parent, delete=False) as file:
        temporary = Path(file.name)
    try:
        temporary.write_text(json.dumps(graph, indent=2), encoding='utf-8')
        temporary.replace(args.output)
    finally:
        temporary.unlink(missing_ok=True)


if __name__ == '__main__':
    main()
