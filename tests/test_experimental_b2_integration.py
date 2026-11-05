"""Offline checks for portable B2 configuration, immutable bundles and demo wiring."""
from copy import deepcopy
import io,json,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch,MagicMock
import numpy as np
from src.experimental.b2 import open_b2,METHOD
from src.experimental.build_bundle import build_bundle,prepare_parents
from src.experimental.search_index import load_artifacts
from src.experimental.demo import main,create_research,load_generator
from tests.test_indexed_research import PASSAGES
from tests.test_token_chunk_experiment import CharacterTokenizer
from tests.test_experimental_b2_retrieval import FakeReranker

class Encoder:
    max_seq_length=256
    tokenizer=CharacterTokenizer()
    def encode(self,texts,**kwargs):return np.zeros((len(texts),384),dtype=np.float32)

class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.path=self.root/'data/processed/candidate'
        self.encoder_path=self.root/'encoder';self.reranker_path=self.root/'reranker'
        self.encoder_path.mkdir();self.reranker_path.mkdir()
        self.encoder=Encoder()
        with patch('src.experimental.build_bundle.ROOT',self.root):
            build_bundle(deepcopy(PASSAGES),self.path,self.encoder)
    def candidate(self):
        return open_b2(self.path,encoder_path=self.encoder_path,reranker_path=self.reranker_path,
                       encoder=self.encoder,reranker=FakeReranker())
    def test_actual_adapter_resolves_original_records(self):
        retrieve,identity,_,provenance=self.candidate()
        hits=retrieve('What findings were reported?',2)
        for hit in hits:self.assertIn(hit,PASSAGES)
        self.assertEqual(provenance['method'],METHOD)
        self.assertEqual(identity()['candidate_algorithm'],METHOD)
        with self.assertRaises(ValueError):retrieve('question',True)
        with self.assertRaises(ValueError):retrieve('x'*300)
    def test_corrupt_bundle_fails_closed(self):
        (self.path/'parents.jsonl').write_text('tampered')
        with self.assertRaisesRegex(ValueError,'changed'):self.candidate()
    def test_missing_models_do_not_fall_back(self):
        with self.assertRaisesRegex(ValueError,'local'):
            open_b2(self.path,encoder_path=self.root/'missing',reranker_path=self.reranker_path)
    def test_invalid_query_vector_rejected(self):
        retrieve,*_=self.candidate()
        self.encoder.encode=lambda *a,**k:np.full((1,384),np.nan)
        with self.assertRaisesRegex(ValueError,'embedding'):retrieve('question')
    def test_existing_output_never_overwritten(self):
        before=(self.path/'manifest.json').read_bytes()
        with patch('src.experimental.build_bundle.ROOT',self.root):
            with self.assertRaisesRegex(ValueError,'NEW'):build_bundle(PASSAGES,self.path,self.encoder)
        self.assertEqual(before,(self.path/'manifest.json').read_bytes())
    def test_live_index_location_refused(self):
        with patch('src.experimental.build_bundle.ROOT',self.root):
            with self.assertRaisesRegex(ValueError,'NEW'):
                build_bundle(PASSAGES,self.root/'data/chroma_db',self.encoder)
    def test_preflight_never_initializes_generation(self):
        candidate=self.candidate()
        with patch('src.experimental.demo.open_b2',return_value=candidate),patch('src.experimental.demo.load_generator') as provider,patch('sys.stdout',new_callable=io.StringIO) as output:
            main(['--bundle',str(self.path),'--encoder',str(self.encoder_path),'--reranker',str(self.reranker_path),'--check-only'])
        provider.assert_not_called();self.assertEqual(json.loads(output.getvalue())['retrieval']['method'],METHOD)
    def test_research_uses_selected_retrieval_provenance(self):
        generate=MagicMock();research=create_research(self.candidate(),generate,{'provider':'fixture'})
        self.assertEqual(research.provenance['retrieval']['method'],METHOD)
        self.assertTrue(research.quality_check);generate.assert_not_called()
    def test_provider_is_explicit(self):
        with patch('src.experimental.demo.open_b2') as retrieval,patch('sys.stderr',new_callable=io.StringIO):
            with self.assertRaises(SystemExit):main(['--bundle','index','--encoder','encoder','--reranker','reranker'])
        retrieval.assert_not_called()
        with self.assertRaises(ValueError):load_generator('malformed',{})
    def test_importing_launcher_does_not_select_original_index(self):
        from src.research_demo import DemoHandler
        before=DemoHandler.research
        create_research(self.candidate(),MagicMock(),{'provider':'fixture'})
        self.assertIs(DemoHandler.research,before)
    def test_separate_server_preserves_original_handler_and_assets(self):
        from src.research_demo import DemoHandler,ASSETS
        previous=DemoHandler.research
        assets={n:(ASSETS/n).read_bytes() for n in ['index.html','app.js','source-reader.js']}
        generator=MagicMock();server=MagicMock();server.server_port=8785
        server.serve_forever.side_effect=KeyboardInterrupt
        with patch('src.experimental.demo.open_b2',return_value=self.candidate()), \
             patch('src.experimental.demo.load_generator',return_value=(generator,{'provider':'fixture'})), \
             patch('src.experimental.demo.ThreadingHTTPServer') as host,patch('sys.stdout',new_callable=io.StringIO):
            host.return_value.__enter__.return_value=server
            main(['--bundle',str(self.path),'--encoder',str(self.encoder_path),'--reranker',str(self.reranker_path),
                  '--generator-factory','fixture:create'])
        handler=host.call_args.args[1]
        self.assertTrue(issubclass(handler,DemoHandler))
        self.assertEqual(handler.research.provenance['retrieval']['method'],METHOD)
        self.assertIs(DemoHandler.research,previous);generator.assert_not_called()
        self.assertEqual(assets,{n:(ASSETS/n).read_bytes() for n in assets})
    def test_source_preparation_preserves_originals(self):
        original=deepcopy(PASSAGES);combined,reports=prepare_parents(original)
        self.assertEqual(combined,PASSAGES);self.assertEqual(reports,[])

if __name__=='__main__':unittest.main()
