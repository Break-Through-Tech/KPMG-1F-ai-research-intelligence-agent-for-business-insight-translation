"""Offline integration regressions; injected providers are not live-provider proof."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from tests.test_indexed_research import adapter
from src.brief_store import BriefStore


class RegulatoryIntegrationTests(unittest.TestCase):
    def test_b2_configures_shared_lazy_assessor(self):
        from src.experimental.demo import create_research
        from src.research_review import assess_regulatory
        from tests.test_indexed_research import PASSAGES, IDENTITY, generator
        retrieval = (lambda q, k: PASSAGES, lambda: IDENTITY, '/test/index', {})
        with patch('src.human_checkpoint.create_client') as client:
            research = create_research(retrieval, generator, {'provider': 'injected'})
            self.assertIs(research.regulatory_assessor, assess_regulatory)
            client.assert_not_called()

    def test_standard_launcher_configures_shared_assessor_without_credentials(self):
        from src.research_demo import main, DemoHandler
        from src.research_review import assess_regulatory
        from tests.test_indexed_research import PASSAGES, IDENTITY, generator
        server = MagicMock()
        with patch('sys.argv', ['demo', '--index', '/test/index', '--codex-model', 'injected', '--no-library']), \
                patch('src.indexed_research.open_index', return_value=(
                    lambda q, k: PASSAGES, lambda: IDENTITY, '/test/index')), \
                patch('src.codex_generation.create_codex_generate', return_value=(generator, {'provider': 'injected'})), \
                patch('src.research_demo.ThreadingHTTPServer', return_value=server), \
                patch('src.human_checkpoint.create_client') as client, \
                patch.object(DemoHandler, 'research', None):
            main()
            self.assertIs(DemoHandler.research.regulatory_assessor, assess_regulatory)
            client.assert_not_called()

    def test_regulatory_failure_survives_save_and_reopen(self):
        def fail(draft):
            raise RuntimeError('injected outage')
        research = adapter(regulatory_assessor=fail)
        envelope = research.execute({'query': 'Compare studies.', 'industry': 'banking',
            'jurisdiction': 'US', 'risk_assessment': True, 'context_id': research.context_id})
        self.assertEqual(envelope['scenario'], 'partial')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'briefs.sqlite'
            saved = BriefStore(path).save(envelope)
            reopened = BriefStore(path).load(saved['library']['brief']['id'])
        for value in (saved, reopened):
            self.assertEqual(value['scenario'], 'partial')
            self.assertEqual(value['error']['stage'], 'regulatory')
            self.assertEqual(value['result']['business_insight']['status'], 'ok')
            self.assertEqual(value['result']['regulatory_checkpoint']['status'], 'failed')
