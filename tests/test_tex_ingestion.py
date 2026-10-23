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
        text = ''.join(c['text'] for c in tex.chunk_source(raw.encode(), AID))
        self.assertNotIn('A', text)
        self.assertIn('B', text)

    def test_explicit_preamble_flags_follow_include_order_without_emitting_preamble(self):
        files = {
            'main.tex': r'''\input{preamble}
\begin{document}
\ifReview HIDDEN_REVIEW\else CLEAN_PAPER\fi
\input{results}
\end{document}''',
            'preamble.tex': r'\def\Clean{1}\input{formatting}',
            'formatting.tex': r'''\newif\ifReview
\ifdefined\Clean\Reviewfalse\else\Reviewtrue\fi
\newcommand{\wrapper}[1]{\ifReview review #1\else clean #1\fi}''',
            'results.tex': r'\ifReview HIDDEN_RESULT\else RESULT_KEPT\fi',
            # An unreachable file must not supply or overwrite flag state.
            'unused.tex': r'\Reviewtrue',
        }
        chunks = tex.chunk_source(archive(files), AID)
        text = '\n'.join(c['text'] for c in chunks)
        self.assertIn('CLEAN_PAPER', text)
        self.assertIn('RESULT_KEPT', text)
        self.assertNotIn('HIDDEN', text)
        self.assertNotIn('wrapper', text)
        self.assertEqual(chunks[0]['line_start'], 3)
        self.assertEqual(chunks[-1]['source_file'], 'results.tex')
        # Definitions after a conditional cannot retroactively decide it.
        files['preamble.tex'] = r'\input{formatting}\def\Clean{1}'
        with self.assertRaises(ValueError):
            tex.chunk_source(archive(files), AID)

    def test_dynamic_macro_and_primitive_reassignment_require_fallback(self):
        for preamble, condition in (
            (r'\newif\ifFlag\def\enable{\csname Flagtrue\endcsname}\enable', r'\ifFlag'),
            (r'\let\iftrue\iffalse', r'\iftrue'),
            (r'\def\iftrue{\iffalse}', r'\iftrue'),
            (r'\def\change{\let\iftrue\iffalse}\change', r'\iftrue'),
        ):
            with self.subTest(preamble=preamble), self.assertRaises(ValueError):
                tex.chunk_source(archive({'main.tex': preamble + r'\begin{document}' + condition +
                    r' YES\else NO\fi\end{document}'}), AID)

    def test_body_mutation_cannot_change_literal_primitive_selection(self):
        for body, extra in (
            (r'\let\iftrue\iffalse\iftrue WRONG\else RIGHT\fi', {}),
            (r'\input{mutate}\iftrue WRONG\else RIGHT\fi',
             {'mutate.tex': r'\let\iftrue\iffalse'}),
        ):
            with self.subTest(body=body), self.assertRaises(ValueError):
                tex.chunk_source(archive({'main.tex': r'\begin{document}' + body +
                    r'\end{document}', **extra}), AID)

    def test_uninspected_include_and_unbraced_macro_arguments_fall_back(self):
        for preamble, condition, extra in (
            (r'{\input{flags}}', r'\iftrue', {'flags.tex': r'\global\let\iftrue\iffalse'}),
            (r'\newif\ifFlag\newcommand{\ignore}[1]{}\ignore\Flagtrue', r'\ifFlag', {}),
        ):
            with self.subTest(preamble=preamble), self.assertRaises(ValueError):
                tex.chunk_source(archive({'main.tex': preamble + r'\begin{document}' + condition +
                    r' WRONG\else RIGHT\fi\end{document}', **extra}), AID)

    def test_deeply_nested_manifest_is_a_fallback_compatible_rejection(self):
        manifest = '{"sources": [{"filename":"main.tex","usage":"toplevel"}],"extra":' + '[' * 20000 + '0' + ']' * 20000 + '}'
        with self.assertRaisesRegex(ValueError, 'nested source manifest'):
            tex.chunk_source(archive({'main.tex': r'\begin{document}Plain\end{document}', '00README.json': manifest}), AID)

    def test_explicit_flag_test_in_preamble_is_not_an_opaque_macro_call(self):
        source = r'\newif\ifFlag\Flagtrue\ifFlag\Flagfalse\fi' + r'\begin{document}\ifFlag WRONG\else RIGHT\fi\end{document}'
        result = tex.chunk_source(archive({'main.tex': source}), AID)
        self.assertIn('RIGHT', str(result))
        self.assertNotIn('WRONG', str(result))

    def test_opaque_aliases_dynamic_discovery_and_control_redefinitions_fall_back(self):
        for preamble, body in (
            (r'\newif\ifFlag\def\ignore#1{}\let\run\ignore\run\Flagtrue', r'\ifFlag WRONG\else RIGHT\fi'),
            (r'\csname let\endcsname\iftrue\iffalse', r'\iftrue WRONG\else RIGHT\fi'),
            (r'\let\else\relax', r'\iftrue FIRST\else SECOND\fi'),
        ):
            with self.subTest(preamble=preamble), self.assertRaises(ValueError):
                tex.chunk_source(archive({'main.tex': preamble + r'\begin{document}' + body + r'\end{document}'}), AID)

    def test_all_macro_declarations_and_aliases_preserve_argument_uncertainty(self):
        for declaration in (r'\edef\ignore#1{}', r'\xdef\ignore#1{}',
                            r'\providecommand{\ignore}[1]{}'):
            for call in (r'\ignore', r'\let\run\ignore\run',
                         r'\let\run\ignore\let\again\run\again'):
                with self.subTest(declaration=declaration, call=call), self.assertRaises(ValueError):
                    source = (r'\newif\ifFlag' + declaration + call + r'\Flagtrue'
                              r'\begin{document}\ifFlag WRONG\else RIGHT\fi\end{document}')
                    tex.chunk_source(archive({'main.tex': source}), AID)

    def test_body_opaque_calls_cannot_consume_conditional_delimiters(self):
        for declaration in (r'\def\ignore#1{}', r'\edef\ignore#1{}',
                            r'\providecommand{\ignore}[1]{}',
                            r'\def\eat#1{}\let\ignore\eat'):
            for body, extra in ((r'\iftrue\ignore\else RIGHT\fi', {}),
                                (r'\iftrue\input{child}\else RIGHT\fi',
                                 {'child.tex': r'\ignore'})):
                with self.subTest(declaration=declaration, body=body), self.assertRaises(ValueError):
                    tex.chunk_source(archive({'main.tex': declaration + r'\begin{document}' +
                        body + r'\end{document}', **extra}), AID)

    def test_unparsed_declaration_families_cannot_establish_branch_state(self):
        for declaration in (r'\newenvironment{unused}{\Flagtrue}{}',
                            r'\NewDocumentCommand{\unused}{}{\Flagtrue}',
                            r'\NewDocumentEnvironment{unused}{}{\Flagtrue}{}'):
            for preamble, body in ((r'\newif\ifFlag' + declaration, r'\ifFlag WRONG\else RIGHT\fi'),
                                   ('', declaration + r'\iftrue FIRST\else SECOND\fi')):
                with self.subTest(declaration=declaration, preamble=preamble), self.assertRaises(ValueError):
                    tex.chunk_source(archive({'main.tex': preamble + r'\begin{document}' + body +
                        r'\end{document}'}), AID)

    def test_indirect_preamble_file_mutations_require_fallback(self):
        for preamble in (
            r'\let\RuntimeFlag\relax\newif\ifFlag\ifdefined\RuntimeFlag\input{flags}\fi',
            r'\newif\ifFlag\def\enable{\input{flags}}\enable',
            r'\newif\ifFlag\def\outer{\inner}\def\inner{\include{flags}}\outer',
        ):
            with self.subTest(preamble=preamble), self.assertRaises(ValueError):
                data = archive({'main.tex': preamble + r'\begin{document}\ifFlag YES\else NO\fi\end{document}',
                               'flags.tex': r'\Flagtrue'})
                tex.chunk_source(data, AID)

    def test_unknown_scoped_and_mutated_state_stays_unresolved(self):
        cases = [
            (r'\newif\ifFlag\ifdefined\Unknown\Flagtrue\fi', ''),
            (r'\newif\ifFlag{\Flagtrue}', ''),
            (r'\newif\ifFlag\begingroup\Flagtrue\endgroup', ''),
            (r'\newif\ifFlag\let\Flagtrue\relax\Flagtrue', ''),
            (r'\newif\ifFlag\def\Flagtrue{}\Flagtrue', ''),
            (r'\newif\ifFlag\def\outer{\inner}\def\inner{\Flagtrue}\outer', ''),
            (r'\newif\ifFlag\def\change{\Flagtrue}\change', ''),
            (r'\newif\ifFlag\def\enable{\Flagtrue}\let\run\enable\run', ''),
            (r'\newif\ifFlag\def\inner{\global\Flagtrue}\def\outer{\inner}{\outer}', ''),
            (r'\newif\ifFlag', r'\Flagtrue'),
            (r'\newif\ifFlag', r'\def\change{\Flagtrue}'),
            (r'\newif\ifFlag', r'\let\alias\Flagtrue\alias'),
        ]
        for preamble, mutation in cases:
            with self.subTest(preamble=preamble, mutation=mutation), self.assertRaises(ValueError):
                files = {'main.tex': preamble + r'\begin{document}\input{child}\ifFlag WRONG\else KEPT\fi\end{document}',
                         'child.tex': mutation}
                tex.chunk_source(archive(files), AID)
        # Positive source facts work, but absence is not proof of undefined.
        raw = r'\def\Known{1}\begin{document}\ifdefined\Known YES\else NO\fi\end{document}'
        text = ''.join(c['text'] for c in tex.chunk_source(raw.encode(), AID))
        self.assertIn('YES', text)
        self.assertNotIn('Known', text)
        self.assertNotIn('NO', text)
        with self.assertRaises(ValueError):
            tex.chunk_source(raw.replace('ifdefined\\Known', 'ifdefined\\Absent').encode(), AID)

    def test_inactive_flag_setters_and_macro_definitions_do_not_change_state(self):
        raw = r'''\newif\ifFlag
\iffalse\Flagtrue\fi
\newcommand{\unused}[1]{\ifFlag \Flagtrue #1\fi}
\begin{document}\ifFlag HIDDEN\else KEPT\fi\end{document}'''
        text = ''.join(c['text'] for c in tex.chunk_source(raw.encode(), AID))
        self.assertIn('KEPT', text)
        self.assertNotIn('HIDDEN', text)

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
