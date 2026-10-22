import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from src.data_ingestion import citation_graph as graph
from tests.test_tex_figures import bundle, paper

AID = '2601.00001v1'
BIB = '''@article{llama, title={The Llama Model}, eprint={2407.21783v2}, archiveprefix={arXiv}}
@article{unused, title={Not cited}, url={https://arxiv.org/pdf/2401.00001.pdf}}
@article{other, title={Non-arxiv}, doi={10.1234/example}}
'''


def document(aid=AID, body=r'\citep[see][p.2]{llama}\nocite{unused}\bibliography{refs}', bib=BIB):
    data = bundle({'main.tex': paper(body), 'refs.bib': bib})
    return dict(arxiv_id=aid, title='Source', source_bytes=data)


class CitationGraphTests(unittest.TestCase):
    def test_exact_metadata_identity_and_citation_provenance(self):
        first = document()
        second = document('2601.00002v1')
        result = graph.build_graph([first, second])
        llama = [n for n in result['nodes'] if n['id'] == 'arxiv:2407.21783']
        self.assertEqual(len(llama), 1)
        cited = [e for e in result['edges'] if e['type'] == 'cites']
        self.assertEqual(len(cited), 2)
        self.assertEqual(cited[0]['arxiv_ids'], ['2407.21783v2'])
        self.assertEqual(cited[0]['source_sha256'], hashlib.sha256(first['source_bytes']).hexdigest())
        self.assertEqual(cited[0]['bibliography_file'], 'refs.bib')
        self.assertEqual(cited[0]['bibliography_line'], 1)
        self.assertEqual(cited[0]['citation_sites'][0]['line'], 3)
        self.assertEqual(cited[0]['citation_sites'][0]['source_file'], 'main.tex')
        self.assertEqual(cited[0]['citation_sites'][0]['command'], 'citep')
        self.assertTrue(any(e['target'] == 'arxiv:2401.00001' and e['type'] == 'bibliography_only'
                            for e in result['edges']))
        candidates = graph.expansion_candidates(result)
        self.assertFalse(candidates['enabled'])
        self.assertEqual(candidates['candidates'], [dict(arxiv_id='2407.21783', citing_papers=2,
                                                       status='candidate_only_not_downloaded')])
        self.assertFalse(result['automatic_expansion'])
        self.assertEqual(graph.arxiv_identifiers({'ID': 'arXiv:2407.21783',
            'title': 'Comparison with arXiv:2401.00001'}), [])
        json.dumps(result, allow_nan=False)

    def test_biblatex_citation_forms_and_inactive_resource(self):
        for command in ('textcite', 'parencite', 'autocite', 'Textcite'):
            with self.subTest(command=command):
                source = paper('\\' + command + '{llama}',
                    r'\iffalse\addbibresource{old.bib}\fi' + '\n' + r'\addbibresource{refs.bib}')
                doc = dict(arxiv_id=AID, source_bytes=bundle({'main.tex': source,
                    'refs.bib': BIB, 'old.bib': BIB}))
                result = graph.build_graph([doc])
                cited = [e for e in result['edges'] if e['type'] == 'cites']
                self.assertEqual(len(cited), 1)
                self.assertEqual(cited[0]['bibliography_file'], 'refs.bib')
                self.assertEqual(cited[0]['citation_sites'][0]['command'], command)
                self.assertEqual(cited[0]['citation_sites'][0]['line'], 4)
                self.assertEqual(len(graph.expansion_candidates(result)['candidates']), 1)

    def test_multicitation_groups_keep_all_keys_and_optional_arguments(self):
        for command in ('cites', 'parencites', 'textcites', 'parencites(see)()'):
            with self.subTest(command=command):
                result = graph.build_graph([document(body='\\' + command + '[see]{llama}[p.2]{unused}' + r'\bibliography{refs}')])
                cited = [e for e in result['edges'] if e['type'] == 'cites']
                self.assertEqual({e['citation_key'] for e in cited}, {'llama', 'unused'})
                self.assertEqual(len(graph.expansion_candidates(result)['candidates']), 2)

    def test_cyclic_and_excessive_string_expressions_stay_inspectable(self):
        cases = [
            '@string{a=b} @string{b=a} @article{llama,journal=a,eprint={2407.21783}}',
            '@string{a0={x}} ' + ' '.join('@string{a%d=a%d}' % (i, i-1) for i in range(1, 40))
                + ' @article{llama,journal=a39,eprint={2407.21783}}',
        ]
        for bib in cases:
            with self.subTest(bib=bib):
                entries = graph._bib_entries('refs.bib', bib)
                self.assertEqual(entries[0]['unresolved_string_fields'], ['journal'])
                result = graph.build_graph([document(bib=bib)])
                self.assertEqual(graph.expansion_candidates(result)['candidates'], [])

    def test_entry_shaped_field_text_does_not_corrupt_bibliography_line(self):
        bib = '@misc{guide, note={Example: @article{llama, title={Example}}}}\n' + BIB
        result = graph.build_graph([document(bib=bib)])
        cited = next(e for e in result['edges'] if e['type'] == 'cites')
        self.assertEqual(cited['bibliography_line'], 2)

    def test_unknown_preamble_bibliography_requires_fallback(self):
        source = paper(r'\cite{llama}', r'\ifdefined\RuntimeFlag\addbibresource{refs.bib}\fi')
        with self.assertRaisesRegex(ValueError, 'Unresolved preamble'):
            graph.build_graph([dict(arxiv_id=AID, source_bytes=bundle({'main.tex': source, 'refs.bib': BIB}))])

    def test_comments_literals_branches_and_case_mismatch(self):
        doc = document(body=r'''% \cite{hidden}
\verb|\cite{literal}|
\iffalse\cite{inactive}\fi
\cite{Llama,missing}\nocite{*}\bibliography{refs}''')
        result = graph.build_graph([doc])
        self.assertEqual(result['papers'][0]['unresolved_keys'], ['Llama', 'missing'])
        self.assertFalse(any(e['type'] == 'cites' for e in result['edges']))
        self.assertEqual(graph.expansion_candidates(result)['candidates'], [])

    def test_duplicates_conflicting_identity_strings_and_no_title_guess(self):
        bib = '''@article{dup,title={One},eprint={2407.21783}}
@article{dup,title={Two},eprint={2407.21783}}
@article{conflict,eprint={2407.21783},url={https://arxiv.org/abs/2401.00001}}
@article{titleonly,title={The Llama Model}}
@article{string,journal=rss,eprint={2407.21783}}'''
        result = graph.build_graph([document(body=r'\cite{dup,conflict,titleonly,string}\bibliography{refs}', bib=bib)])
        self.assertEqual(result['papers'][0]['duplicate_keys'], ['dup'])
        self.assertTrue(all(e['identity_status'] == 'unresolved_or_provisional' for e in result['edges']))
        self.assertEqual([e['bibliography_line'] for e in result['edges'][:2]], [1, 2])
        self.assertEqual(graph.expansion_candidates(result)['candidates'], [])
        self.assertEqual(result['edges'][-1]['unresolved_string_fields'], ['journal'])

    def test_biblatex_preamble_inline_and_root_matched_bbl(self):
        source = paper(r'\cite{llama}', r'\addbibresource{refs.bib}')
        data = bundle({'main.tex': source, 'refs.bib': BIB})
        self.assertEqual(graph.bibliography(data)['selected_bib'], ['refs.bib'])
        body = r'\cite{key}\begin{thebibliography}{9}\bibitem{key} Model arXiv:2407.21783\end{thebibliography}'
        result = graph.build_graph([dict(arxiv_id=AID, source_bytes=paper(body).encode())])
        self.assertEqual(result['edges'][0]['format'], 'inline_bibitem')
        self.assertEqual(result['edges'][0]['target'], 'arxiv:2407.21783')
        data = bundle({'main.tex': paper(r'\cite{key}\bibliography{missing}'),
                       'old.bbl': r'\bibitem{wrong} arXiv:2401.00001',
                       'main.bbl': r'\bibitem{key} arXiv:2407.21783'})
        result = graph.build_graph([dict(arxiv_id=AID, source_bytes=data)])
        self.assertEqual(result['papers'][0]['bbl_candidates'], ['main.bbl'])
        self.assertEqual(result['edges'][0]['format'], 'root_bbl_candidate')
        self.assertEqual(result['edges'][0]['identity_status'], 'unresolved_or_provisional')
        self.assertNotIn('wrong', str(result))
        self.assertEqual(graph.expansion_candidates(result)['candidates'], [])

    def test_ambiguous_mismatched_root_malformed_and_bounds(self):
        data = bundle({'dir/main.tex': paper(r'\bibliography{refs}\cite{llama}'),
                       'dir/refs.bib': BIB, 'refs.bib': BIB, 'old.bbl': r'\bibitem{llama} Wrong'})
        # Only root/containing directories are candidates; unrelated top-level
        # entries are not guessed. A nested include creates real ambiguity.
        self.assertEqual(graph.bibliography(data)['selected_bib'], ['dir/refs.bib'])
        data = bundle({'main.tex': paper(r'\input{section/body}'),
                       'section/body.tex': r'\bibliography{refs}\cite{llama}',
                       'section/refs.bib': BIB, 'refs.bib': BIB})
        layer = graph.bibliography(data)
        self.assertEqual(layer['ambiguous_declared_bib'], ['refs.bib'])
        self.assertEqual(layer['entries'], [])
        result = graph.build_graph([document(bib='@article{broken,title={incomplete}')])
        self.assertTrue(result['papers'][0]['parse_errors'])
        duplicate = graph.build_graph([document(bib='@string{x={A}}\n@string{x={B}}\n' + BIB)])
        self.assertEqual(duplicate['edges'][0]['duplicate_string_definitions'], ['x'])
        affected = graph.build_graph([document(bib='@string{x={A}}\n@string{x={B}}\n@article{k,journal=x,eprint={2407.21783}}')])
        self.assertEqual(affected['edges'][0]['unresolved_string_fields'], ['journal'])
        self.assertEqual(affected['edges'][0]['identity_status'], 'unresolved_or_provisional')
        self.assertEqual(graph.base_id('Math.gt/9901001v2'), 'math.gt/9901001')
        self.assertEqual(result['edges'], [])
        for name in ('MAX_RECORDS', 'MAX_SITES', 'MAX_GRAPH_BYTES'):
            with patch.object(graph, name, 0), self.assertRaises(ValueError):
                graph.build_graph([document()])
        with self.assertRaises(ValueError):
            graph.build_graph([document(), document()])
        for limit in (-1, 11, True):
            with self.assertRaises(ValueError):
                graph.expansion_candidates({}, limit)

    def test_cli_keeps_arxiv_identity_before_sentence_punctuation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source.tex'
            source.write_text(paper(r'\cite{k}\begin{thebibliography}{9}\bibitem{k} Example. arXiv:2407.21783.\end{thebibliography}'))
            output = root / 'graph.json'
            result = subprocess.run([sys.executable, '-m', 'src.data_ingestion.citation_graph',
                '--source', f'{AID}={source}', '--output', str(output)], capture_output=True, text=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(output.read_text())
            self.assertEqual(data['edges'][0]['target'], 'arxiv:2407.21783')
            self.assertEqual(data['expansion_candidates']['candidates'][0]['arxiv_id'], '2407.21783')
            self.assertEqual(graph.arxiv_identifiers({'raw': 'arXiv:2407.21783.123'}), [])

    def test_cli_offline_atomic_output_and_failure_preserves_previous(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / 'source.bin'
            path.write_bytes(document()['source_bytes'])
            output = root / 'graph.json'
            cmd = [sys.executable, '-m', 'src.data_ingestion.citation_graph', '--source', f'{AID}={path}', '--output', str(output)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stderr)
            previous = output.read_bytes()
            self.assertEqual(len(json.loads(previous)['edges']), 3)
            path.write_bytes(b'invalid source')
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(output.read_bytes(), previous)
