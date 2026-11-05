"""Parent fidelity across the semantic/B2 integration boundary."""
from copy import deepcopy
from unittest.mock import patch
import numpy as np
from tests.test_experimental_b2_integration import IntegrationTests, Encoder
from tests.test_experimental_html_evidence import page, th, extract
from src.experimental.build_bundle import build_bundle, prepare_parents
from src.experimental.html_evidence import validate_source_bindings
from src.experimental.search_chunks import collapse_to_parents
from src.experimental.search_index import load_artifacts
from src.experimental.semantic_views import make_semantic_views


class SemanticEncoder(Encoder):
    def encode(self, texts, **kwargs):
        return np.ones((len(texts), 384), dtype=np.float32)


class SemanticIntegrationTests(IntegrationTests):
    def setUp(self):
        super().setUp()
        self.encoder = SemanticEncoder()

    def test_semantic_bundle_retrieves_original_parents(self):
        from tests.test_semantic_chunking_adapter import passage
        parents = [passage()]
        before = deepcopy(parents)
        path = self.path.parent / 'semantic'
        with patch('src.experimental.build_bundle.ROOT', self.root):
            manifest = build_bundle(parents, path, self.encoder, strategy='semantic95_token224_parent')
        _, restored, views, _, _ = load_artifacts(path)
        self.assertEqual(parents, before)
        self.assertEqual(restored, before)
        self.assertEqual(manifest['strategy'], 'semantic95_token224_parent')
        for view in views:
            self.assertEqual(view['text'], parents[0]['text'][view['char_start']:view['char_end']])
        old = self.path
        self.path = path
        retrieve, _, _, provenance = self.candidate()
        self.assertEqual(retrieve('What improves?', 1), parents)
        self.assertEqual(provenance['strategy'], 'semantic95_token224_parent')
        self.path = old

    def test_table_is_not_semantically_split_and_source_binding_survives(self):
        html = page([th('Model') + th('Score'), '<td>A</td><td>0.9</td>'])
        parents = extract(html)['passages']
        before = deepcopy(parents)
        with patch('src.experimental.semantic_views.chunk_passages', side_effect=AssertionError('Must preserve table row')):
            views = make_semantic_views(parents, self.encoder)
        restored = collapse_to_parents(views, [0.] * len(views), parents)
        self.assertEqual(restored[0]['text'], before[0]['text'])
        self.assertEqual(parents, before)
        validate_source_bindings(parents, html, '2601.00001v1', 'Paper')
        bad = deepcopy(views)
        bad[0]['text'] = 'changed'
        with self.assertRaises(ValueError):
            collapse_to_parents(bad, [0.] * len(bad), parents)
