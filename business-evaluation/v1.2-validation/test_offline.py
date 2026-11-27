"""Exercise the validation package with injected responses only."""

import csv
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock
import zipfile

import runner
import score


def canned(prompt):
    industry = next(line.split(': ', 1)[1] for line in prompt.splitlines()
                    if line.startswith('Industry or capability: '))
    return json.dumps({'status': 'insufficient_evidence', 'industry': industry, 'implications': [],
                       'risks': [], 'limitations': ['The supplied evidence does not establish enterprise ROI.']})


class ValidationTests(unittest.TestCase):
    def test_preflight_pins_inputs_and_comparators(self):
        result = runner.preflight(runner.DEFAULT_PDFS)
        self.assertEqual(result['planned_calls'], 16)
        self.assertEqual(result['saved_comparators'], 24)
        self.assertFalse(result['provider_contacted'])

    def test_final_schedule_and_blind_adjudication(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            directory = root / 'fixture'
            generate = Mock(side_effect=canned)
            records = runner.run_candidates(directory, generate, {'execution': 'offline_fixture'}, pace=0)
            self.assertEqual(generate.call_count, 16)
            self.assertEqual(len(list((directory / 'ledger').glob('*.json'))), 16)
            self.assertEqual(records['U7']['attempts'], 0)
            self.assertEqual(records['U7']['status'], 'skipped_no_accepted_evidence')
            with self.assertRaises(FileExistsError):
                runner.run_candidates(directory, generate, {}, pace=0)
            self.assertEqual(generate.call_count, 16)
            archive_path = runner.export_blind(directory, records)
            with zipfile.ZipFile(archive_path) as archive:
                self.assertEqual(len(archive.namelist()), 61)
                self.assertNotIn('blind-key.json', archive.namelist())
                template = list(csv.DictReader(io.StringIO(archive.read('scores.csv').decode())))
                self.assertEqual(len(template), 41)
                singleton_cases = sum(sum(r['blind_case'] == case for r in template) == 1
                                      for case in {r['blind_case'] for r in template})
                self.assertEqual(singleton_cases, 5)
            outcomes = score.load_blind(directory)
            sheets = []
            first_item = next(item for item, status in outcomes.items() if status == 'ok')
            for n in (1, 2):
                sheet = root / f'scores-{n}.csv'
                with sheet.open('x', encoding='utf-8', newline='') as file:
                    writer = csv.DictWriter(file, fieldnames=list(template[0]))
                    writer.writeheader()
                    for row in template:
                        key = (row['blind_case'], row['output_label'])
                        status = outcomes[key]
                        dim = 'NA' if status in score.MISSING else 4
                        fields = dict.fromkeys(score.DIMS, dim)
                        if n == 2 and key == first_item:
                            fields['fidelity'] = 2
                        writer.writerow({**row, **fields, 'reviewer_id': f'AI_FIXTURE_{n}',
                                         **dict.fromkeys(score.DEFECTS, 0),
                                         **dict.fromkeys(score.OBSERVATIONS, 'not_applicable'),
                                         'critical_unsupported_claim': 'no',
                                         'appropriate_abstention': 'yes' if status in score.ABSTAINS else 'not_applicable'})
                sheets.append(sheet)
            self.assertEqual(score.collect(directory, *sheets), 1)
            with self.assertRaises((AssertionError, ValueError)):
                score.finalize(directory)
            review = directory / 'ai-review'
            self.assertFalse((review / 'blind-consensus.json').exists())
            adjudication = review / 'adjudication.csv'
            rows = score.read_csv(adjudication)
            rows[0].update(final=4, evidence_citation='fixture', rationale='fixture')
            with adjudication.open('w', encoding='utf-8', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=score.ADJUDICATION)
                writer.writeheader()
                writer.writerows(rows)
            score.finalize(directory)
            result = runner.read(review / 'metrics-unblinded.json')
            self.assertEqual(result['groups']['known/baseline']['available'], 11)
            self.assertEqual(result['groups']['known/v1.1']['available'], 6)
            self.assertEqual(result['groups']['fresh/v1.2']['available'], 0)
            self.assertEqual(result['fresh_pairing'], 'not_applicable')
            self.assertTrue(result['quality_gates']['known']['zero_call_empty_control'])
            self.assertFalse(result['all_applicable_quality_gates_met'])

    def test_provider_failure_stops_remaining_calls_and_keeps_control(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / 'fixture'
            generate = Mock(side_effect=RuntimeError('provider failure'))
            records = runner.run_candidates(directory, generate, {}, pace=0, order=list(runner.packets()))
            self.assertEqual(generate.call_count, 1)
            self.assertEqual(records['R1']['status'], 'execution_failed')
            self.assertEqual(records['F5']['status'], 'not_run_after_provider_failure')
            self.assertEqual(records['U7']['attempts'], 0)


if __name__ == '__main__':
    unittest.main()
