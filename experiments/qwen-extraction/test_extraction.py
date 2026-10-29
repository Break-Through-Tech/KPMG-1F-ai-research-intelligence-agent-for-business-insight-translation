"""Offline checks for leakage-sensitive selection and extraction scoring boundaries."""
import unittest

from evaluate import deterministic, anchors
from prepare import select_quote


class ExtractionChecks(unittest.TestCase):
    def setUp(self):
        self.evidence = [{"chunk_id": "2601.00001v1_c0000", "text": "We compare\nmodels using a blinded rubric."},
                         {"chunk_id": "2601.00001v1_c0001", "text": "Accuracy reached 80%."}]

    def test_valid_alternative_not_reference_equality(self):
        self.assertTrue(deterministic('"using a blinded rubric." [2601.00001v1_c0000]', self.evidence)["pass"])

    def test_whitespace_is_not_a_paraphrase(self):
        self.assertTrue(deterministic('We compare models using a blinded rubric. (chunk_id: "2601.00001v1_c0000")', self.evidence)["pass"])

    def test_known_but_wrong_citation_fails(self):
        self.assertFalse(deterministic('"Accuracy reached 80%." [2601.00001v1_c0000]', self.evidence)["pass"])

    def test_added_claim_fails_even_with_valid_quote(self):
        self.assertFalse(deterministic('"Accuracy reached 80%." [2601.00001v1_c0001] This proves deployment readiness.', self.evidence)["pass"])

    def test_word_repair_is_not_whitespace_normalization(self):
        evidence = [{"chunk_id": "2601.00001v1_c0000", "text": "We use\npost-\ngeneration checks."}]
        self.assertFalse(deterministic('"We use post-generation checks." [2601.00001v1_c0000]', evidence)["pass"])

    def test_literal_finding_requires_semantic_judge(self):
        self.assertTrue(deterministic('"Accuracy reached 80%." [2601.00001v1_c0001]', self.evidence)["pass"])
        negative = anchors()[1]
        self.assertEqual(negative["expected"], "fail")
        self.assertTrue(deterministic(negative["answer"], negative["evidence"])["pass"])

    def test_ambiguous_source_selector_fails(self):
        with self.assertRaises(ValueError):
            select_quote("We compare models. We compare reviewers.", "We compare", "models.")

    def test_source_selection_retains_exact_bytes(self):
        self.assertEqual(select_quote("Header. We compare\nmodels. Tail.", "We compare", "models."), "We compare\nmodels.")


if __name__ == "__main__":
    unittest.main()
