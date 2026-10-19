import gzip
import hashlib
import io
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from src.data_ingestion import config, pipeline, tex_source as tex
from src.research_contracts import validate_evidence


def archive(files):
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode='w:gz') as tar:
        for name, text in files.items():
            data = text.encode()
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    return stream.getvalue()


ROOT = r'''\documentclass{article}
\newcommand{\foo}{not expanded}
\begin{document}
\section{Results}
Evidence before the include.
\input{sections/results}
Evidence after the include.
\end{document}
'''
RESULT = r'''Equation evidence: \[s(x)=\frac{x-a}{b-a}\]
An escaped percent is 10\%. % drop this comment
'''
AID = '2601.00001v1'
ROW = dict(arxiv_id=AID, title='Research', authors='Author', abstract='Abstract',
           categories='cs.AI', published='2026-01-01', updated='2026-01-02',
           pdf_url=f'https://arxiv.org/pdf/{AID}')


class TexIngestionTests(unittest.TestCase):
    def test_multifile_math_and_locators(self):
        data = archive({'paper.tex': ROOT, 'sections/results.tex': RESULT})
        chunks = tex.chunk_source(data, AID, 'Research')
        self.assertEqual([c['source_file'] for c in chunks],
                         ['paper.tex', 'sections/results.tex', 'paper.tex'])
        self.assertIn(r'\[s(x)=\frac{x-a}{b-a}\]', chunks[1]['text'])
        self.assertIn(r'10\%', chunks[1]['text'])
        self.assertNotIn('drop this comment', chunks[1]['text'])
        self.assertNotIn('not expanded', ''.join(c['text'] for c in chunks))
        self.assertEqual(chunks[1]['line_start'], 1)
        self.assertEqual(chunks[1]['source_sha256'], hashlib.sha256(data).hexdigest())
        for chunk in chunks:
            validate_evidence([{**chunk, **ROW}])
            self.assertIsNone(chunk['page_number'])
            self.assertNotIn('html_url', chunk)

    def test_single_and_gzip_tex(self):
        source = ROOT.replace(r'\input{sections/results}', RESULT).encode()
        for data in (source, gzip.compress(source)):
            self.assertTrue(tex.chunk_source(data, AID))

    def test_reject_missing_cyclic_ambiguous_or_unsupported_includes(self):
        cases = [
            {'main.tex': ROOT},
            {'main.tex': ROOT, 'other.tex': ROOT},
            {'main.tex': ROOT, 'sections/results.tex': r'\input{../main}'},
            {'main.tex': ROOT.replace(r'\input{sections/results}', r'\input missing')},
            {'main.tex': ROOT.replace(r'\end{document}', '')},
            {'main.tex': ROOT.replace(r'\input{sections/results}', r'\iffalse hidden\fi')},
            {'main.tex': ROOT.replace(r'\input{sections/results}', r'\begin{verbatim}x\end{verbatim}')},
        ]
        for files in cases:
            with self.subTest(files=list(files)), self.assertRaises(ValueError):
                tex.chunk_source(archive(files), AID)

    def test_paths_links_duplicates_and_limits(self):
        for path in ('../evil.tex', '/evil.tex', 'dir/../../evil.tex', r'dir\evil.tex'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                tex.read_source(archive({path: ROOT}))
        stream = io.BytesIO()
        with tarfile.open(fileobj=stream, mode='w') as tar:
            info = tarfile.TarInfo('main.tex')
            info.type = tarfile.SYMTYPE
            info.linkname = '/etc/passwd'
            tar.addfile(info)
        with self.assertRaises(ValueError):
            tex.read_source(stream.getvalue())
        with patch.object(tex, 'MAX_EXPANDED', 10), self.assertRaises(ValueError):
            tex.read_source(gzip.compress(b'x' * 100))
        with patch.object(tex, 'MAX_ARCHIVE', 10), self.assertRaises(ValueError):
            tex.read_source(b'x' * 11)
        with patch.object(tex, 'MAX_MEMBERS', 0), self.assertRaises(ValueError):
            tex.read_source(archive({'main.tex': ROOT}))

    def test_ids_cannot_escape_cache_or_change_host(self):
        for aid in ('../evil', 'https://evil.test', '2601.00001?x=1'):
            with self.assertRaises(ValueError):
                tex.cache_path(aid)
        self.assertEqual(tex.cache_path('cs/9901001v2').name, 'cs_9901001v2.source')

    def test_opt_in_pipeline_and_atomic_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / 'chunks.parquet'
            output.write_bytes(b'previous corpus')
            data = archive({'main.tex': ROOT, 'sections/results.tex': RESULT})
            (root / f'{AID}.source').write_bytes(data)
            with patch.object(config, 'TEX_DIR', root), \
                 patch.object(pipeline, 'load_html', return_value=None), \
                 patch.object(pipeline, 'resolve_pdf_path', return_value=None):
                with self.assertRaises(RuntimeError):
                    pipeline.process_and_store([ROW], output)
                self.assertEqual(output.read_bytes(), b'previous corpus')
                result = pipeline.process_and_store([ROW], output, use_tex=True)
                stored = pd.read_parquet(output)
                self.assertEqual(set(result.source), {'tex'})
                self.assertEqual(set(stored.source_sha256), {hashlib.sha256(data).hexdigest()})
                self.assertTrue(stored.page_number.isna().all())
                (root / f'{AID}.source').write_bytes(b'%PDF-not-source')
                before = output.read_bytes()
                with self.assertRaises(RuntimeError):
                    pipeline.process_and_store([ROW], output, use_tex=True)
                self.assertEqual(output.read_bytes(), before)

    def test_failed_tex_falls_back_to_pdf_and_html_keeps_priority(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / f'{AID}.source').write_bytes(b'not tex')
            pages = [{'page': 2, 'text': 'Valid PDF fallback evidence. ' * 30}]
            with patch.object(config, 'TEX_DIR', root), \
                 patch.object(pipeline, 'load_html', return_value=None), \
                 patch.object(pipeline, 'resolve_pdf_path', return_value=root / 'paper.pdf'), \
                 patch.object(pipeline, 'extract_pages', return_value=pages):
                result = pipeline.process_and_store([ROW], root / 'out.parquet', use_tex=True)
                self.assertEqual(set(result.source), {'pdf'})
            html = '<section class="ltx_section"><h2 class="ltx_title">Results</h2><div class="ltx_para">' + 'Evidence. ' * 30 + '</div></section>'
            with patch.object(pipeline, 'load_html', return_value=html), \
                 patch.object(pipeline, 'chunk_source') as parse:
                result = pipeline.process_and_store([ROW], root / 'out.parquet', use_tex=True)
                self.assertEqual(set(result.source), {'html'})
                parse.assert_not_called()

    def test_download_cache_and_validation(self):
        from unittest.mock import MagicMock
        data = archive({'main.tex': ROOT.replace(r'\input{sections/results}', RESULT)})
        response = MagicMock()
        response.__enter__.return_value = response
        response.status_code = 200
        response.iter_content.return_value = [data]
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(config, 'TEX_DIR', Path(directory)), \
             patch.object(tex.requests, 'get', return_value=response) as get:
            tex.download_sources([ROW], delay=0)
            self.assertEqual(tex.cache_path(AID).read_bytes(), data)
            tex.download_sources([ROW], delay=0)
            self.assertEqual(get.call_count, 1)
            tex.cache_path(AID).unlink()
            response.iter_content.return_value = [b'<html>error</html>']
            tex.download_sources([ROW], delay=0)
            self.assertFalse(tex.cache_path(AID).exists())

    def test_citation_metadata_roundtrip(self):
        from src.retrieval import citation_metadata
        data = archive({'main.tex': ROOT.replace(r'\input{sections/results}', RESULT)})
        chunk = {**tex.chunk_source(data, AID)[0], **ROW}
        metadata = citation_metadata(chunk)
        validate_evidence([{**metadata, 'text': chunk['text'], 'chunk_id': chunk['chunk_id'], 'page_number': None}])
        self.assertEqual(metadata, citation_metadata(metadata))
        for key, value in (('line_start', 0), ('line_end', -1), ('source_url', ROW['pdf_url'])):
            with self.subTest(key=key), self.assertRaises(ValueError):
                citation_metadata({**chunk, key: value})
