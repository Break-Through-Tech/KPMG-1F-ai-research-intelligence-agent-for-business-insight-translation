"""Source fidelity and model-profile regressions; no network or model downloads."""
import copy
import unittest
from src.semantic_chunking_adapter import EmbeddingAdapter, chunk_passages
from src.research_contracts import validate_evidence
from src.data_ingestion.tex_source import chunk_source

AID = '2601.00001v1'
PDF = f'https://arxiv.org/pdf/{AID}'


def passage(source='pdf', **changes):
    row = dict(chunk_id='parent', text='Agent planning improves tool selection. Clinical outcomes improve for patients.',
               title='Research', arxiv_id=AID, pdf_url=PDF, source=source,
               source_url=PDF+'#page=2', page_number=2, section='results')
    if source == 'html':
        row.update(page_number=None, html_url=f'https://arxiv.org/html/{AID}#S2',
                   source_url=f'https://arxiv.org/html/{AID}#S2', subsection='Evaluation')
    row.update(changes)
    return row


class Encoder:
    def encode(self, texts, **kwargs):
        return [(0., 1.) if 'Clinical' in t else (1., 0.) for t in texts]


class AdapterTests(unittest.TestCase):
    def test_ingestion_metadata_conversion_matches_documented_adapter_boundary(self):
        from src.retrieval import citation_metadata
        raw = [passage(), passage('html', chunk_id='html')]
        for row in raw:
            row.pop('source_url')
        evidence = [{'page_number': None, **citation_metadata(row),
                     'chunk_id': row['chunk_id'], 'text': row['text']} for row in raw]
        chunks = chunk_passages(evidence, Encoder())
        validate_evidence(chunks)
        self.assertEqual({'pdf', 'html'}, {c['source'] for c in chunks})

    def test_pdf_page_boundaries_and_original_text_are_preserved(self):
        rows = [passage(distance=0.25), passage(chunk_id='page3', page_number=3, source_url=PDF+'#page=3')]
        before = copy.deepcopy(rows)
        chunks = chunk_passages(rows, Encoder())
        self.assertEqual(4, len(chunks))
        self.assertEqual(rows, before)
        for c in chunks:
            parent = next(p for p in rows if p['chunk_id'] == c['parent_chunk_id'])
            self.assertEqual(c['source_url'], parent['source_url'])
            self.assertNotIn('distance', c)
            self.assertEqual(c['page_number'], parent['page_number'])
            self.assertEqual(c['text'], parent['text'][c['parent_text_start']:c['parent_text_end']])
        validate_evidence(chunks)

    def test_html_anchor_subsection_and_source_structure_are_retained(self):
        row = passage('html', source_html='<p>Retained whole-source context</p>')
        chunks = chunk_passages([row], Encoder())
        self.assertEqual(2, len(chunks))
        for c in chunks:
            self.assertEqual(row['html_url'], c['source_url'])
            self.assertEqual(row['subsection'], c['subsection'])
            self.assertEqual(row['source_html'], c['source_html'])
            self.assertIsNone(c['page_number'])
        validate_evidence(chunks)

    def test_real_tex_ingestor_output_preserves_math_and_child_line_locations(self):
        raw = (r'\documentclass{article}'+'\n'+r'\begin{document}'+'\n'
               + 'Agent planning evidence.\nClinical outcomes for patients.\n'
               + r'\[x = 1.0 + 2.0 + 3.0 + 4.0 + 5.0 + 6.0\]'+'\n'
               + 'More agent evidence.\n'+r'\end{document}').encode()
        parents = [dict(p, title='Research', pdf_url=PDF) for p in chunk_source(raw, AID, 'Research')]
        before = copy.deepcopy(parents)
        chunks = chunk_passages(parents, Encoder(), max_chars=30)
        self.assertEqual(before, parents)
        equation = r'\[x = 1.0 + 2.0 + 3.0 + 4.0 + 5.0 + 6.0\]'
        self.assertEqual(1, sum(equation in c['text'] for c in chunks))
        self.assertTrue(next(c for c in chunks if equation in c['text'])['oversized_math'])
        for c in chunks:
            p = next(p for p in parents if p['chunk_id'] == c['parent_chunk_id'])
            self.assertEqual(p['source_file'], c['source_file'])
            self.assertEqual(p['source_sha256'], c['source_sha256'])
            self.assertEqual(p['line_start'] + p['text'].count('\n', 0, c['parent_text_start']), c['line_start'])
            self.assertEqual(c['line_start'] + c['text'].count('\n'), c['line_end'])
            self.assertEqual(p['text'][c['parent_text_start']:c['parent_text_end']], c['text'])
        validate_evidence(chunks)

    def test_tex_literals_with_punctuation_are_atomic(self):
        row = passage(source='tex', page_number=None, source_url=f'https://arxiv.org/src/{AID}',
                      source_file='main.tex', source_sha256='a'*64, line_start=10, line_end=12,
                      text='Before.\n\\verb|a.b.c.d.e.f.g.h.i.j|\nAfter.')
        chunks = chunk_passages([row], Encoder(), max_chars=8)
        self.assertEqual(1, sum(r'\verb|a.b.c.d.e.f.g.h.i.j|' in c['text'] for c in chunks))

    def test_malformed_tex_is_rejected_not_split_as_plain_text(self):
        row = passage(source='tex', page_number=None, source_url=f'https://arxiv.org/src/{AID}',
                      source_file='main.tex', source_sha256='a'*64, line_start=1, line_end=1,
                      text=r'Before. \[unclosed equation')
        with self.assertRaises(ValueError):
            chunk_passages([row], Encoder())

    def test_figure_assets_stay_whole_without_embedding_or_fabricated_paper_page(self):
        row = passage(source='tex_figure', page_number=None, source_url=f'https://arxiv.org/src/{AID}',
                      source_sha256='a'*64, asset_sha256='b'*64, asset_file='plot.pdf',
                      asset_page_number=2, extraction_method='pdf_text',
                      evidence_scope='whole_bundled_asset_not_rendered_figure')
        class NoEncode:
            def encode(self, *a, **k):raise AssertionError('Asset should stay whole')
        self.assertEqual([row], chunk_passages([row], NoEncode(), max_chars=4))

    def test_duplicate_parent_ids_and_wrong_pdf_page_are_rejected(self):
        for rows in ([passage(), passage()], [passage(page_number=3)]):
            with self.assertRaises(ValueError):chunk_passages(rows, Encoder())

    def test_invalid_vectors_do_not_discard_source_text(self):
        for bad in ([], [(0.,0.),(1.,0.)], [(float('nan'),1.),(1.,0.)], [(1.,),(1.,2.)]):
            class Bad:
                def encode(self,*a,**k):return bad
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                chunk_passages([passage()], Bad())

    def test_cancelled_centroid_makes_boundary_instead_of_losing_content(self):
        class Opposite:
            def encode(self,*a,**k):return [(1.,0.),(-1.,0.),(1.,0.)]
        row = passage(text='First. Second. Third.')
        chunks = chunk_passages([row], Opposite(), similarity_threshold=-1)
        self.assertEqual(['First. Second.', 'Third.'], [c['text'] for c in chunks])

    def test_untrusted_or_impossible_settings_are_rejected(self):
        for opts in ({'max_chars':True}, {'max_chars':0}, {'similarity_threshold':float('nan')},
                     {'similarity_threshold':True}, {'similarity_threshold':2}):
            with self.subTest(opts=opts), self.assertRaises(ValueError):chunk_passages([passage()], Encoder(), **opts)

    def test_e5_separates_symmetric_similarity_from_query_passage_retrieval(self):
        calls=[]
        class Spy:
            def encode(self,texts,**kwargs):calls.append((texts,kwargs));return [(1.,0.)]*len(texts)
        a = EmbeddingAdapter(Spy(),'intfloat/e5-small-v2')
        a.encode(['sentence']);a.encode_queries(['question']);a.encode_passages(['evidence'])
        self.assertEqual([['query: sentence'], ['query: question'], ['passage: evidence']], [c[0] for c in calls])
        self.assertTrue(all(c[1]['normalize_embeddings'] for c in calls))
        self.assertEqual('query: ', a.provenance()['sentence_prefix'])

    def test_bge_instruction_is_query_only_and_minilm_has_no_prefix(self):
        for model, prefix in [('BAAI/bge-small-en-v1.5','Represent this sentence for searching relevant passages: '),
                              ('sentence-transformers/all-MiniLM-L6-v2','')]:
            calls=[]
            class Spy:
                def encode(self,texts,**kw):calls.append(texts);return [(1.,0.)]*len(texts)
            a=EmbeddingAdapter(Spy(),model)
            a.encode(['sentence']);a.encode_queries(['question']);a.encode_passages(['evidence'])
            self.assertEqual([['sentence'],[prefix+'question'],['evidence']], calls)
        with self.assertRaises(ValueError):EmbeddingAdapter(Encoder(),'unknown/model')
