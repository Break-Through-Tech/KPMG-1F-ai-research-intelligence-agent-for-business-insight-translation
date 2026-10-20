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
            {'main.tex': ROOT.replace(r'\input{sections/results}', r'\ifnum 1=2 hidden\fi')},
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

    def test_corrupt_deflate_download_continues_and_cached_source_uses_pdf(self):
        from unittest.mock import MagicMock
        bad = bytes.fromhex('1f8b0800000000000003ff')
        with self.assertRaisesRegex(ValueError, 'Corrupt gzip'):
            tex.read_source(bad)
        good = archive({'main.tex': ROOT.replace(r'\input{sections/results}', RESULT)})
        response = MagicMock()
        response.__enter__.return_value = response
        response.status_code = 200
        response.iter_content.side_effect = [[bad], [good]]
        second = {**ROW, 'arxiv_id': '2601.00002v1'}
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(config, 'TEX_DIR', Path(directory)), \
             patch.object(tex.requests, 'get', return_value=response):
            tex.download_sources([ROW, second], delay=0)
            self.assertFalse(tex.cache_path(AID).exists())
            self.assertEqual(tex.cache_path(second['arxiv_id']).read_bytes(), good)
            tex.cache_path(AID).write_bytes(bad)
            pages = [{'page': 2, 'text': 'Valid PDF fallback evidence. ' * 30}]
            with patch.object(pipeline, 'load_html', return_value=None), \
                 patch.object(pipeline, 'resolve_pdf_path', return_value=Path(directory) / 'paper.pdf'), \
                 patch.object(pipeline, 'extract_pages', return_value=pages):
                result = pipeline.process_and_store([ROW], Path(directory) / 'out.parquet', use_tex=True)
                self.assertEqual(set(result.source), {'pdf'})

    def test_math_is_atomic_even_when_larger_than_target_chunk(self):
        from src.data_ingestion.tex_chunking import split_tex
        expressions = [r'\[' + 'x + ' * 600 + r'y\]',
                       '$$' + 'x + ' * 600 + 'y$$',
                       r'\begin{align*}' + 'x + ' * 600 + r'y\end{align*}',
                       r'\begin {equation}' + 'x + ' * 600 + r'y\end {equation}',
                       r'\(' + 'x + ' * 600 + r'y\)',
                       '$' + 'x + ' * 600 + 'y$']
        for expression in expressions:
            with self.subTest(delimiter=expression[:15]):
                text = ('Definitions and assumptions. ' * 90 + '\n' + expression
                        + '\n' + 'Consequences of this equation. ' * 90)
                pieces = list(split_tex(text))
                owners = [piece for piece in pieces if expression in piece['text']]
                self.assertTrue(owners)
                self.assertTrue(all(piece['oversized_math'] for piece in owners))
                for piece in pieces:
                    self.assertEqual(piece['text'], text[piece['start_index']:piece['start_index'] + len(piece['text'])])
                    if 'x + ' in piece['text']:
                        self.assertIn(expression, piece['text'])
                self.assertTrue(any('Definitions' in piece['text'] for piece in owners))

    def test_unterminated_or_pathologically_large_math_is_rejected(self):
        from src.data_ingestion import tex_chunking
        for text in (r'\[unclosed', r'\begin{equation}unclosed', '$unclosed'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                list(tex_chunking.split_tex(text))
        with patch.object(tex_chunking, 'MAX_MATH', 20), self.assertRaises(ValueError):
            list(tex_chunking.split_tex(r'\[' + 'x' * 30 + r'\]'))
        pieces = list(tex_chunking.split_tex(r'Costs 10\% and \$5. ' * 200))
        self.assertFalse(any(piece['oversized_math'] for piece in pieces))

    def test_tex_citation_helper_in_direct_script_import_environment(self):
        import json, subprocess, sys
        data = archive({'main.tex': ROOT.replace(r'\input{sections/results}', RESULT)})
        chunk = {**tex.chunk_source(data, AID)[0], **ROW}
        script = Path(__file__).resolve().parents[1] / 'src' / 'retrieval.py'
        command = ("import runpy,json; namespace=runpy.run_path(" + repr(str(script))
                   + "); print(json.dumps(namespace['citation_metadata']("
                   + repr(chunk) + ")))" )
        result = subprocess.run([sys.executable, '-I', '-c', command],
                                capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['source'], 'tex')

    def test_generation_context_omits_tex_instead_of_truncating_math(self):
        from src.summarization import _build_context
        text = r'\[' + 'x + ' * 600 + r'y\]'
        passage = dict(source='tex', chunk_id='eq', text=text)
        for context_limit, passage_limit in ((5000, 500), (500, 5000)):
            context, included, omitted = _build_context([passage], context_limit, passage_limit)
            self.assertEqual(context, '')
            self.assertEqual(included, [])
            self.assertEqual(omitted, ['eq'])
        context, included, omitted = _build_context([passage], 5000, 5000)
        self.assertIn(text, context)
        self.assertFalse(included[0][1])
        self.assertFalse(omitted)

    def test_manifest_selects_paper_not_bundled_template_or_revision(self):
        import json
        paper = ROOT.replace(r'\input{sections/results}', 'Actual paper evidence.')
        manifest = json.dumps({'sources': [dict(usage='toplevel', filename='arxiv.tex')]})
        data = archive({'arxiv.tex': paper, 'main.tex': paper.replace('Actual', 'Template'),
                        'old.tex': paper, '00README.json': manifest})
        chunks = tex.chunk_source(data, AID)
        self.assertEqual({c['source_file'] for c in chunks}, {'arxiv.tex'})
        for value in (None, {'sources': [{'usage': 'toplevel'}]},
                      {'sources': [dict(usage='toplevel', filename='../bad.tex')]},
                      {'sources': [dict(usage='toplevel', filename='missing.tex')]},
                      {'sources': [dict(usage='toplevel', filename='arxiv.tex'),
                                   dict(usage='toplevel', filename='main.tex')]},
                      {'sources': 'invalid'}):
            with self.subTest(manifest=value), self.assertRaises(ValueError):
                tex.source_blocks(archive({'arxiv.tex': paper, '00README.json': json.dumps(value)}))

    def test_literals_are_opaque_atomic_and_keep_percent_and_line_locators(self):
        literals = [r'\verb|50% $unmatched \input{missing} \fi|',
                    r'\verb*+\begin{document}+',
                    '\\begin{verbatim}\n50% $unmatched \\input{missing}\n\\end{verbatim}',
                    '\\begin{lstlisting}\nx = "$" # 50%\n\\end{lstlisting}',
                    '\\begin{minted}{python}\nx = "$" # 50%\n\\end{minted}']
        for literal in literals:
            body = '\\begin{document}\n' + literal + '\nAFTER\n\\end{document}'
            chunks = tex.chunk_source(body.encode(), AID)
            self.assertTrue(any(literal in c['text'] for c in chunks))
            for c in chunks:
                lines = body.splitlines()[c['line_start']-1:c['line_end']]
                self.assertIn(c['text'], '\n'.join(lines))
        from src.data_ingestion.tex_chunking import split_tex
        with self.assertRaisesRegex(ValueError, 'literal exceeds'):
            list(split_tex(r'\begin{verbatim}' + 'x' * 33000 + r'\end{verbatim}'))
        literal = '\\begin{verbatim}\n' + 'x%$\\input{missing} ' * 150 + '\n\\end{verbatim}'
        pieces = list(split_tex('Before.\n' + literal + '\nAfter.'))
        self.assertTrue(any(literal in p['text'] and p['oversized_math'] for p in pieces))
        for malformed in (r'\verb|unclosed', r'\begin{verbatim}unclosed'):
            with self.assertRaises(ValueError):
                tex.chunk_source(('\\begin{document}' + malformed + '\\end{document}').encode(), AID)

    def test_comments_and_constant_branches_do_not_publish_hidden_text(self):
        body = r'''\begin{document}
START
\begin{comment}
\begin{document}\input{missing} $unmatched
\end{comment}
\iffalse HIDDEN \input{missing} \iftrue NESTED\else STILL_HIDDEN\fi
\else KEPT\fi
\iftrue TRUE\else FALSE\fi
% OMITTED
END
\end{document}'''
        chunks = tex.chunk_source(body.encode(), AID)
        text = '\n'.join(c['text'] for c in chunks)
        for hidden in ('HIDDEN', 'NESTED', 'FALSE', 'OMITTED', 'missing', 'unmatched'):
            self.assertNotIn(hidden, text)
        for kept in ('START', 'KEPT', 'TRUE', 'END'):
            self.assertIn(kept, text)
        self.assertEqual(body.count('\n'), tex._uncomment(body).count('\n'))
        for bad in (r'\iffalse x', r'\fi', r'\iftrue x\else y\else z\fi',
                    r'\ifdefined\foo x\else y\fi', r'\ifnum1=1 x\fi',
                    r'\unless\iftrue HIDDEN\else KEPT\fi'):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                tex.chunk_source(('\\begin{document}' + bad + '\\end{document}').encode(), AID)

    def test_macro_names_are_not_primitive_conditions_and_custom_conditions_fail_closed(self):
        raw = r'\begin{document}\ifplotsrgb{A}{B}\ifdefempty{X}{}{Y}\end{document}'
        self.assertIn(r'\ifplotsrgb', tex.chunk_source(raw.encode(), AID)[0]['text'])
        with self.assertRaisesRegex(ValueError, 'Conditional macro includes'):
            tex.chunk_source(archive({'main.tex': r'\begin{document}\ifthenelse{X}{\input{a}}{\input{b}}\end{document}',
                                      'a.tex': 'Branch A', 'b.tex': 'Branch B'}), AID)
        raw = r'\newif\ifCameraReview\begin{document}\ifCameraReview A\else B\fi\end{document}'
        with self.assertRaises(ValueError):
            tex.chunk_source(raw.encode(), AID)

    def test_larger_asset_bundles_still_have_separate_text_and_expansion_bounds(self):
        paper = r'\begin{document}Paper evidence\end{document}'
        data = archive({'main.tex': paper, 'image.bin': 'x' * 1000})
        self.assertTrue(tex.chunk_source(data, AID))
        with patch.object(tex, 'MAX_TEX', 10), self.assertRaises(ValueError):
            tex.read_source(data)
        with patch.object(tex, 'MAX_EXPANDED', 100), self.assertRaises(ValueError):
            tex.read_source(data)
        with patch.object(tex, 'MAX_TEX', 10), self.assertRaises(ValueError):
            tex.read_source(gzip.compress(paper.encode()))
