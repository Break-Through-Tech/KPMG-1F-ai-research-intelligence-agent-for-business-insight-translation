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

    def test_unknown_preamble_path_state_requires_fallback(self):
        source = paper(r'\includegraphics{sample.pdf}',
                       r'\ifdefined\RuntimeFlag\graphicspath{{live/}}\fi')
        with self.assertRaisesRegex(ValueError, 'Unresolved preamble'):
            figures.extract_figure_text(bundle({'main.tex': source,
                'live/sample.pdf': pdf('UNPROVEN')}), AID)

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
