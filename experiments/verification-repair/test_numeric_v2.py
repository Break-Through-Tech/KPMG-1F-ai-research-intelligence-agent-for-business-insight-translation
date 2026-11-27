"""v2 number check: each correction releases its development case AND the protection it touches still holds.

Development cases are verbatim from business-multiagent-v1 held claims (development data, not validation).
Protection cases are constructed misstatements of the same sources. Run: python -I test_numeric_v2.py
"""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / 'agentic')]
import numeric_checks_v2 as nc  # noqa: E402


def check(text, *quotes, context=()):
    nc._CONTEXT = tuple(context)
    try:
        return nc.ground_text(text, list(quotes))
    finally:
        nc._CONTEXT = ()


TABLE = ('Fine-tune / Dataset: IS; Method: Ctrl; Llama-3-8B / ASR: 32.7%; Llama-2-7B / ASR: 43.3%; '
         'Vicuna-7B / ASR: 57.1%; ChatGLM-6B / ASR: 71.5%')
KG = ('In the distractor setting, where irrelevant chunks are limited, our proposed method achieves similar performance '
      'in recall but significantly better performance in precision (more than 7.9% and 6.9% on HotpotQA and '
      'Shuffle-HotpotQA, respectively).')
MASK = ('Specifically, after applying 30%, 50%, and 70% relationship masking, the F1 score of MultiRAG on the Books '
        'dataset only dropped from 66.8% to 60.0%.')
ROW = ('Architecture: Hybrid Retrieval and Reranking (Cohere); Chunk Type: Ctx; Prec: 43.0; Recall: 70.3; F1-score: 44.1; '
       'Mean Latency (s): 10.39')
FMTI = 'Based on Figure 5.5 , the highest-scoring developer scores points for 54 of the 100 indicators, and the average score across all developers is 37.'


class Releases(unittest.TestCase):
    def test_r1_postfix_subjects_in_a_list(self):
        r = check('Residual attack success rates were 32.7% for Llama-3-8B, 43.3% for Llama-2-7B, 57.1% for '
                  'Vicuna-7B, and 71.5% for ChatGLM-6B.', TABLE)
        self.assertEqual(r['contradictions'], [])

    def test_r4_model_version_is_a_name(self):
        src = 'a relatively small model ( Llama-3.1-8B-Instruct ) can be trained to match performance of a much larger frontier model ( claude-3-5-sonnet ).'
        r = check('The trained Llama-3.1-8B-Instruct agent was competitive with Claude 3.5 Sonnet.', src)
        self.assertEqual(r['contradictions'], [])

    def test_r8_respectively(self):
        r = check('Distractor-setting precision improved by more than 7.9% on HotpotQA and 6.9% on Shuffle-HotpotQA.', KG)
        self.assertEqual(r['contradictions'], [])

    def test_r3_emphatic_only(self):
        r = check("Under 30%, 50% and 70% masking, MultiRAG's F1 on Books fell from 66.8% to 60.0%.", MASK)
        self.assertEqual(r['contradictions'], [])

    def test_r2_r5_table_row(self):
        r = check('With Cohere, F1 was 44.1 and mean latency 10.39 seconds; precision/recall were 43.0/70.3.', ROW)
        self.assertEqual(r['contradictions'], [])

    def test_r6_stated_base(self):
        self.assertEqual(check('The average score was 37/100, with the leader at 54.', FMTI)['contradictions'], [])

    def test_r1_figure_label_is_not_a_subject(self):
        src = 'our SeqQA tasks require 7-10 LLM calls (Figure 5 ) and cost $0.07 on average per trajectory'
        self.assertEqual(check('SeqQA tasks needed 7-10 calls and cost $0.07 per trajectory.', src)['contradictions'], [])


class StillProtected(unittest.TestCase):
    def test_swapped_table_attribution(self):
        r = check('Residual attack success was 43.3% for Llama-3-8B and 32.7% for Llama-2-7B.', TABLE)
        self.assertIn('subject_mismatch', r['contradictions'])

    def test_explicit_swap_in_prose(self):
        r = check('Model X reached 78.0% and Model Y reached 64.5%.', 'Model X reached 64.5% and Model Y reached 78.0%.')
        self.assertIn('subject_mismatch', r['contradictions'])

    def test_respectively_swap(self):
        r = check('Precision improved by more than 6.9% on HotpotQA and 7.9% on Shuffle-HotpotQA.', KG)
        self.assertIn('subject_mismatch', r['contradictions'])

    def test_versioned_models_stay_distinct(self):
        r = check('GPT-4o scored 86.4% on the benchmark.', 'GPT-4 scored 86.4% on the benchmark, while GPT-4o scored 88.7%.')
        self.assertIn('subject_mismatch', r['contradictions'])

    def test_unknown_model_size_is_still_a_number(self):
        src = 'Qwen Pro Finance 32B outperforms the base Llama 70B model in both languages.'
        r = check('Qwen Pro Finance 14B outperforms the base Llama 70B model.', src, context=[src])
        self.assertIn('numbers_absent', r['contradictions'])

    def test_explicit_metric_swap(self):
        r = check('Distractor-setting recall improved by more than 7.9% on HotpotQA.', KG)
        self.assertIn('metric_mismatch', r['contradictions'])

    def test_f1_versus_accuracy(self):
        self.assertIn('metric_mismatch', check('MultiRAG reached 66.8% accuracy.', 'MultiRAG reached an F1 score of 66.8%.')['contradictions'])

    def test_real_only_condition_must_be_kept(self):
        src = 'MultiRAG improved F1 by 10.2% only on the Books dataset.'
        self.assertIn('missing_condition', check('MultiRAG improved F1 by 10.2%.', src)['contradictions'])

    def test_header_unit_mismatch(self):
        self.assertIn('unit_mismatch', check('Cohere had a mean latency of 10.39 ms.', ROW)['contradictions'])

    def test_wrong_denominator(self):
        self.assertIn('denominator_error', check('The leader scored 54/120.', FMTI)['contradictions'])

    def test_ratio_against_a_different_source_ratio(self):
        self.assertIn('denominator_error', check('18/25 participants agreed.', '18 of 20 participants agreed.')['contradictions'])

    def test_value_absent(self):
        self.assertIn('numbers_absent', check('MultiRAG on Books fell from 66.8% to 59.0%.', MASK)['contradictions'])

    def test_year_not_in_quote_is_still_held(self):
        src = 'developers performed best on indicators in the downstream domain, scoring 65% of available points overall'
        self.assertIn('numbers_absent', check('The 2024 results show downstream scored 65%.', src)['contradictions'])

    def test_reversed_direction(self):
        self.assertIn('reversed_comparison', check("ChatKBQA's F1 rose from 59.1% to 53.0%.", "ChatKBQA's F1 score dropped from 59.1% to 53.0%.")['contradictions'])


if __name__ == '__main__':
    unittest.main()
