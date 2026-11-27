from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from capture import Capture, CaptureError, STAGES, run_question
from test_agentic import Provider, Retriever, draft, plan, verdicts


class CaptureTests(unittest.TestCase):
    def test_real_path_with_fake_provider_persists_trace_and_final(self):
        from test_agentic import X
        fake = Provider(plan=[plan()], research=[draft(X)], verify=[verdicts(("supported", []))])
        retriever = Retriever({"Model X": ["A1"]})
        with TemporaryDirectory() as tmp:
            result = run_question(Path(tmp), {"id": "fixture", "question": "What did Model X score?"},
                                  retriever, fake, lambda: {"indexed_records_sha256": "fixture"}, [])
            self.assertEqual(result["attempts"], list(STAGES[:3]))
            self.assertFalse(result["integrity_violation"])
            self.assertEqual(result["answer"]["result"]["summary"]["claims"][0]["text"], X["text"])
            folder = Path(tmp) / "fixture"
            for filename in ("synthesis-1.evidence.json", "agentic.json", "result.json"):
                self.assertTrue((folder / filename).is_file())

    def test_wrong_stage_and_duplicate_folders_fail_closed(self):
        with TemporaryDirectory() as tmp:
            target = Path(tmp) / "fixture"
            capture = Capture(target, lambda *_: self.fail("Unexpected provider invocation"))
            with self.assertRaises(CaptureError):
                capture("Synthesize an answer", response_schema={})
            with self.assertRaises(FileExistsError):
                Capture(target, None)


if __name__ == "__main__":
    unittest.main()
