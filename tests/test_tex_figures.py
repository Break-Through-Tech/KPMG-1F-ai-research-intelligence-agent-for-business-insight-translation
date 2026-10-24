import gzip
import hashlib
import io
import json
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pymupdf

from src.data_ingestion import pipeline, tex_assets, tex_figures as figures
from src.data_ingestion.tex_source import chunk_source
from src.research_contracts import validate_evidence
from tests.test_tex_ingestion import AID, ROW


def bundle(files):
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode='w:gz') as tar:
        for name, value in files.items():
            data = value.encode() if isinstance(value, str) else value
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    return stream.getvalue()


def pdf(*texts):
    with pymupdf.open() as doc:
        for text in texts:
            page = doc.new_page()
            if text:
                page.insert_text((72, 72), text)
        return doc.tobytes()


def paper(body, preamble=''):
    return preamble + '\n' + r'\begin{document}' + '\n' + body + '\n' + r'\end{document}'


class FigureTextTests(unittest.TestCase):
    def test_recovery_dedup_and_provenance(self):
        asset = pdf('Prompt starts at LS Apartment', 'Final plan')
        source = paper(r'\includegraphics[page=2,trim=0 0 20 20,clip]{images/sample}' + '\n'
                       + r'\includegraphics{images/sample.pdf}')
        data = bundle({'main.tex': source, 'images/sample.pdf': asset,
                       'unused.pdf': pdf('UNUSED')})
        result = figures.extract_figure_text(data, AID, ROW['title'])
        self.assertEqual(len(result['chunks']), 2)
        self.assertEqual(len(result['coverage']), 2)
        self.assertEqual({x['status'] for x in result['coverage']}, {'text_extracted'})
        self.assertNotIn('UNUSED', str(result))
        for chunk in result['chunks']:
            self.assertEqual(chunk['source_sha256'], hashlib.sha256(data).hexdigest())
            self.assertEqual(chunk['asset_sha256'], hashlib.sha256(asset).hexdigest())
            self.assertIsNone(chunk['page_number'])
            self.assertNotIn('line_start', chunk)
            self.assertIn('whole_bundled_asset', chunk['evidence_scope'])
            validate_evidence([{**chunk, **ROW}])
        self.assertIn('Prompt starts at LS Apartment', result['chunks'][0]['text'])
        self.assertNotIn('Prompt starts', str(chunk_source(data, AID)))

    def test_inactive_preamble_graphicspath_never_selects_unused_asset(self):
        source = paper(r'\includegraphics{sample.pdf}',
                       r'\graphicspath{{live/}}\iffalse\graphicspath{{unused/}}\fi')
        data = bundle({'main.tex': source, 'live/sample.pdf': pdf('ACTIVE'),
                       'unused/sample.pdf': pdf('INACTIVE')})
        result = figures.extract_figure_text(data, AID)
        self.assertEqual(result['coverage'][0]['asset_file'], 'live/sample.pdf')
        self.assertIn('ACTIVE', result['chunks'][0]['text'])
        self.assertNotIn('INACTIVE', str(result))

    def test_uncalled_preamble_macro_does_not_select_its_graphicspath(self):
        source = paper(r'\includegraphics{sample.pdf}',
            r'\graphicspath{{live/}}\newcommand{\unused}{\graphicspath{{unused/}}}')
        data = bundle({'main.tex': source, 'live/sample.pdf': pdf('ACTIVE'),
                       'unused/sample.pdf': pdf('INACTIVE')})
        result = figures.extract_figure_text(data, AID)
        self.assertEqual(result['coverage'][0]['asset_file'], 'live/sample.pdf')
        with self.assertRaises(ValueError):
            figures.extract_figure_text(bundle({'main.tex': source.replace(r'\begin{document}',
                r'\unused\begin{document}'), 'live/sample.pdf': pdf('ACTIVE'),
                'unused/sample.pdf': pdf('INACTIVE')}), AID)

    def test_scoped_preamble_paths_require_fallback(self):
        for scoped in (r'{\graphicspath{{unused/}}}',
                       r'\begingroup\graphicspath{{unused/}}\endgroup'):
            with self.subTest(scoped=scoped), self.assertRaisesRegex(ValueError, 'Scoped preamble'):
                source = paper(r'\includegraphics{sample.pdf}', r'\graphicspath{{live/}}' + scoped)
                figures.extract_figure_text(bundle({'main.tex': source,
                    'live/sample.pdf': pdf('ACTIVE'), 'unused/sample.pdf': pdf('INACTIVE')}), AID)

    def test_body_path_mutations_across_blocks_never_publish_frozen_asset(self):
        for body, extra in ((r'\graphicspath{{other/}}\includegraphics{sample.pdf}', {}),
                            (r'\input{paths}\includegraphics{sample.pdf}',
                             {'paths.tex': r'\graphicspath{{other/}}'})):
            with self.subTest(body=body):
                data = bundle({'main.tex': paper(body, r'\graphicspath{{live/}}'),
                    'live/sample.pdf': pdf('STALE'), 'other/sample.pdf': pdf('CURRENT'), **extra})
                result = figures.extract_figure_text(data, AID)
                self.assertEqual(result['chunks'], [])
                self.assertEqual(result['coverage'][0]['status'], 'unsupported_source_semantics')

    def test_body_macro_call_cannot_publish_a_stale_asset_path(self):
        for body, extra in ((r'\switch\includegraphics{sample.pdf}', {}),
                            (r'\input{paths}\includegraphics{sample.pdf}', {'paths.tex': r'\switch'})):
            with self.subTest(body=body):
                source = paper(body, r'\graphicspath{{live/}}\newcommand{\switch}{\graphicspath{{other/}}}')
                result = figures.extract_figure_text(bundle({'main.tex': source,
                    'live/sample.pdf': pdf('STALE'), 'other/sample.pdf': pdf('CURRENT'), **extra}), AID)
                self.assertEqual(result['chunks'], [])
                self.assertEqual(result['coverage'][0]['status'], 'unsupported_source_semantics')

    def test_dynamic_body_path_changes_cannot_publish_stale_text(self):
        for body, extra in ((r'\csname graphicspath\endcsname{{other/}}\includegraphics{sample.pdf}', {}),
                            (r'\input{paths}\includegraphics{sample.pdf}',
                             {'paths.tex': r'\csname graphicspath\endcsname{{other/}}'})):
            with self.subTest(body=body):
                result = figures.extract_figure_text(bundle({'main.tex': paper(body, r'\graphicspath{{live/}}'),
                    'live/sample.pdf': pdf('STALE'), 'other/sample.pdf': pdf('CURRENT'), **extra}), AID)
                self.assertEqual(result['chunks'], [])
                self.assertEqual(result['coverage'][0]['status'], 'unsupported_source_semantics')

    def test_unknown_preamble_path_state_requires_fallback(self):
        source = paper(r'\includegraphics{sample.pdf}',
                       r'\ifdefined\RuntimeFlag\graphicspath{{live/}}\fi')
        with self.assertRaisesRegex(ValueError, 'Unresolved preamble'):
            figures.extract_figure_text(bundle({'main.tex': source,
                'live/sample.pdf': pdf('UNPROVEN')}), AID)

    def test_preamble_graphics_rules_cannot_select_unused_default_extension(self):
        source = paper(r'\includegraphics{fig}',
                       r'\DeclareGraphicsExtensions{.alt}\DeclareGraphicsRule{.alt}{pdf}{.alt}{}')
        with self.assertRaises(ValueError):
            figures.extract_figure_text(bundle({'main.tex': source,
                'fig.alt': pdf('ACTIVE'), 'fig.pdf': pdf('UNUSED EVIDENCE')}), AID)

    def test_active_references_graphicspath_and_explicit_gaps(self):
        source = paper(r'''\iffalse\includegraphics{hidden.pdf}\fi
% \includegraphics{comment.pdf}
\verb|\includegraphics{literal.pdf}|
\includegraphics{visible}
\includegraphics{raster.png}
\includegraphics{blank.pdf}
\includegraphics{missing}
\includegraphics{dynamic/\name.pdf}
\includegraphics not-braced
''', r'\graphicspath{{figures/}}')
        result = figures.extract_figure_text(bundle({'main.tex': source,
            'figures/visible.pdf': pdf('Visible text'), 'raster.png': b'not decoded',
            'blank.pdf': pdf(''), 'hidden.pdf': pdf('HIDDEN')}), AID)
        self.assertEqual(len(result['coverage']), 6)
        self.assertEqual(len(result['chunks']), 1)
        statuses = {x['status'] for x in result['coverage']}
        self.assertEqual(statuses, {'text_extracted', 'needs_visual_extraction',
                                   'missing_or_ambiguous', 'unsupported_reference', 'unsupported_syntax'})
        self.assertNotIn('HIDDEN', str(result))

    def test_unexecuted_macros_and_unknown_branch_arguments_are_not_figure_evidence(self):
        for body in (r'\newcommand{\unused}{\includegraphics{fig.pdf}}',
                     r'\ifthenelse{unknown}{\includegraphics{fig.pdf}}{}'):
            result = figures.extract_figure_text(bundle({'main.tex': paper(body),
                                                         'fig.pdf': pdf('Not proven active')}), AID)
            self.assertEqual(result['chunks'], [])
            self.assertEqual(result['coverage'][0]['status'], 'unsupported_source_semantics')

    def test_unexecuted_environment_definitions_never_publish_figure_text(self):
        for command in ('newenvironment', 'renewenvironment'):
            definition = '\\' + command + r'{unused}{\includegraphics{hidden.pdf}}{}'
            for included in (False, True):
                with self.subTest(command=command, included=included):
                    files = {'main.tex': paper(r'\input{child}' if included else definition),
                             'hidden.pdf': pdf('UNUSED EVIDENCE')}
                    if included:
                        files['child.tex'] = definition
                    result = figures.extract_figure_text(bundle(files), AID)
                    self.assertEqual(result['chunks'], [])
                    self.assertEqual(result['coverage'][0]['status'], 'unsupported_source_semantics')
            with self.subTest(command=command, location='preamble'), self.assertRaises(ValueError):
                figures.extract_figure_text(bundle({'main.tex': paper(
                    r'\includegraphics{sample.pdf}', '\\' + command +
                    r'{unused}{\graphicspath{{unused/}}}{}'),
                    'unused/sample.pdf': pdf('UNUSED EVIDENCE')}), AID)

    def test_document_command_and_environment_declarations_never_publish_unused_assets(self):
        for prefix in ('New', 'Renew', 'Provide', 'Declare'):
            for kind in ('Command', 'Environment'):
                target = r'{\unused}' if kind == 'Command' else '{unused}'
                definition = ('\\' + prefix + 'Document' + kind + target +
                              r'{}{\includegraphics{hidden.pdf}}' + ('{}' if kind == 'Environment' else ''))
                for included in (False, True):
                    with self.subTest(prefix=prefix, kind=kind, included=included):
                        files = {'main.tex': paper(r'\input{child}' if included else definition),
                                 'hidden.pdf': pdf('UNUSED EVIDENCE')}
                        if included:
                            files['child.tex'] = definition
                        result = figures.extract_figure_text(bundle(files), AID)
                        self.assertEqual(result['chunks'], [])
                        self.assertEqual(result['coverage'][0]['status'], 'unsupported_source_semantics')

    def test_uppercase_conditionals_never_publish_unresolved_branch_assets(self):
        for body, extra in ((r'\IfFileExists{absent.txt}{\includegraphics{hidden.pdf}}{}', {}),
                            (r'\input{child}', {'child.tex':
                             r'\IfFileExists{absent.txt}{\includegraphics{hidden.pdf}}{}'}),
                            (r'\IfBooleanTF{\flag}{\includegraphics{hidden.pdf}}{}', {})):
            with self.subTest(body=body):
                result = figures.extract_figure_text(bundle({'main.tex': paper(body),
                    'hidden.pdf': pdf('UNUSED EVIDENCE'), **extra}), AID)
                self.assertEqual(result['chunks'], [])
                self.assertEqual(result['coverage'][0]['status'], 'unsupported_source_semantics')

    def test_quoted_commands_never_publish_asset_text(self):
        for quoted in (r'\string\includegraphics{hidden.pdf}',
                       r'\detokenize{\includegraphics{hidden.pdf}}',
                       r'\noexpand\includegraphics{hidden.pdf}',
                       r'\meaning\includegraphics{hidden.pdf}'):
            for included in (False, True):
                with self.subTest(quoted=quoted, included=included):
                    files = {'main.tex': paper(r'\input{child}' if included else quoted),
                             'hidden.pdf': pdf('UNUSED EVIDENCE')}
                    if included:
                        files['child.tex'] = quoted
                    with self.assertRaises(ValueError):
                        figures.extract_figure_text(bundle(files), AID)

    def test_terminated_child_requires_fallback_before_figure_publication(self):
        data = bundle({'main.tex': paper(r'\input{child}' + '\n' + r'\includegraphics{visible.pdf}'),
                       'child.tex': '\\endinput\n' + r'\includegraphics{hidden.pdf}',
                       'hidden.pdf': pdf('UNUSED EVIDENCE'), 'visible.pdf': pdf('VISIBLE EVIDENCE')})
        with self.assertRaisesRegex(ValueError, 'input termination'):
            figures.extract_figure_text(data, AID)
        # The termination may precede another input: block-local rejection is
        # insufficient because that input has a different source filename.
        data = bundle({'main.tex': paper(r'\input{child}\includegraphics{visible.pdf}'),
                       'child.tex': '\\endinput\n' + r'\input{hidden}',
                       'hidden.tex': r'\includegraphics{hidden.pdf}',
                       'hidden.pdf': pdf('UNUSED EVIDENCE'), 'visible.pdf': pdf('VISIBLE EVIDENCE')})
        with self.assertRaisesRegex(ValueError, 'input termination'):
            figures.extract_figure_text(data, AID)

    def test_stored_graphics_tokens_are_not_executed_references(self):
        for included in (False, True):
            with self.subTest(included=included):
                body = r'\toks0={\includegraphics{hidden.pdf}}'
                files = {'main.tex': paper(r'\input{child}' if included else body),
                         'hidden.pdf': pdf('UNUSED EVIDENCE')}
                if included:
                    files['child.tex'] = body
                with self.assertRaises(ValueError):
                    figures.extract_figure_text(bundle(files), AID)

    def test_named_token_register_allocations_require_fallback(self):
        for allocation in (r'\newtoks\stash', r'\toksdef\stash=0'):
            for included in (False, True):
                with self.subTest(allocation=allocation, included=included):
                    body = r'\stash={\includegraphics{hidden.pdf}}'
                    files = {'main.tex': paper(r'\input{child}' if included else body, allocation),
                             'hidden.pdf': pdf('UNUSED EVIDENCE')}
                    if included:
                        files['child.tex'] = body
                    with self.assertRaises(ValueError):
                        figures.extract_figure_text(bundle(files), AID)

    def test_included_document_termination_disables_all_figure_publication(self):
        for ending in (r'\end{document}', r'\end {document}'):
            with self.subTest(ending=ending):
                with self.assertRaisesRegex(ValueError, 'input termination'):
                    figures.extract_figure_text(bundle({
                        'main.tex': paper(r'\input{child}\includegraphics{parent.pdf}'),
                        'child.tex': ending + r'\includegraphics{hidden.pdf}',
                        'hidden.pdf': pdf('UNUSED EVIDENCE'), 'parent.pdf': pdf('UNREACHABLE PARENT')}), AID)

    def test_ambiguous_unsafe_corrupt_and_limits(self):
        source = paper(r'\includegraphics{fig}')
        result = figures.extract_figure_text(bundle({'main.tex': source,
            'fig.pdf': pdf('PDF'), 'fig.png': b'PNG'}), AID)
        self.assertEqual(result['coverage'][0]['status'], 'missing_or_ambiguous')
        result = figures.extract_figure_text(bundle({'main.tex': paper(r'\includegraphics{bad.pdf}'),
                                                     'bad.pdf': b'broken'}), AID)
        self.assertEqual(result['coverage'][0]['status'], 'extraction_failed')
        self.assertEqual(result['chunks'], [])
        with self.assertRaises(ValueError):
            figures.extract_figure_text(bundle({'../bad.pdf': b'', 'main.tex': source}), AID)
        data = bundle({'main.tex': source, 'fig.pdf': pdf('page one', 'page two')})
        for target, name, value in ((figures, 'MAX_PAGES', 1), (figures, 'MAX_TEXT', 1)):
            with patch.object(target, name, value):
                result = figures.extract_figure_text(data, AID)
                self.assertEqual(result['chunks'], [])
                self.assertEqual(result['coverage'][0]['status'], 'extraction_failed')
        with patch.object(figures, 'MAX_FIGURES', 0), self.assertRaises(ValueError):
            figures.extract_figure_text(data, AID)
        for bound in ('MAX_ASSET', 'MAX_ASSET_TOTAL'):
            with patch.object(tex_assets, bound, 1), self.assertRaises(ValueError):
                figures.extract_figure_text(data, AID)

    def test_pipeline_opt_in_parquet_and_retrieval_round_trip(self):
        from src.retrieval import citation_metadata
        from src.agent import source_location
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = bundle({'main.tex': paper(r'\includegraphics{fig.pdf}'),
                           'fig.pdf': pdf('Recovered embedded prompt')})
            (root / (AID + '.source')).write_bytes(data)
            with patch.object(pipeline.cfg, 'TEX_DIR', root), patch.object(pipeline, 'load_html', return_value=None):
                plain = pipeline.process_and_store([ROW], root / 'plain.parquet', use_tex=True)
                self.assertEqual(set(plain.source), {'tex'})
                result = pipeline.process_and_store([ROW], root / 'fig.parquet', use_tex=True, use_tex_figures=True)
            self.assertEqual(set(result.source), {'tex', 'tex_figure'})
            figure = result[result.source == 'tex_figure'].iloc[0].to_dict()
            metadata = citation_metadata(figure)
            from src.summarization import _build_context
            context, _, _ = _build_context([{**figure, **metadata}], 10000, 5000)
            self.assertIn('NOT rendered paper figure/page', context)
            self.assertIn('fig.pdf', context)
            validate_evidence([{**metadata, 'page_number': None, 'chunk_id': figure['chunk_id'], 'text': figure['text']}])
            self.assertEqual(metadata['asset_page_number'], 1)
            self.assertIn('not a paper page', source_location(metadata))
            self.assertEqual(json.loads(figure['figure_coverage'])[0]['status'], 'text_extracted')
            for field in ('asset_sha256', 'asset_page_number', 'evidence_scope'):
                damaged = {**metadata, 'page_number': None, 'chunk_id': 'x', 'text': 'evidence'}
                damaged.pop(field)
                with self.assertRaises(ValueError):
                    validate_evidence([damaged])
        with self.assertRaises(ValueError):
            pipeline.process_and_store([ROW], use_tex_figures=True)

    def test_duplicate_asset_and_plain_gzip_sources(self):
        stream = io.BytesIO()
        with tarfile.open(fileobj=stream, mode='w') as tar:
            for name, value in [('main.tex', paper('body').encode()), ('x.pdf', b'1'), ('x.pdf', b'2')]:
                info = tarfile.TarInfo(name)
                info.size = len(value)
                tar.addfile(info, io.BytesIO(value))
        with self.assertRaises(ValueError):
            figures.extract_figure_text(stream.getvalue(), AID)
        for value in (paper('body').encode(), gzip.compress(paper('body').encode())):
            self.assertEqual(figures.extract_figure_text(value, AID), {'chunks': [], 'coverage': []})
