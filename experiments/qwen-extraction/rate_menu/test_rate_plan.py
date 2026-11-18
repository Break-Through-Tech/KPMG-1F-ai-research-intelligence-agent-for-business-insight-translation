import json
import unittest
from decimal_wire import checked_parse


class RatePlan(unittest.TestCase):
    def test_contrasts(self):
        for initial, final, op, value, unit in [
            ('0', '17', 'point_change', '17', 'percentage points'),
            ('37.5', '37.5', 'relative_change', '0', '%'),
            ('15', '21', 'relative_change', '40.0', '%'),
            ('21', '15', 'point_change', '-6', 'percentage points'),
        ]:
            with self.subTest(initial=initial, final=final, operation=op):
                case = {'evidence': [{'chunk_id': 'a', 'text': f'From {initial}% to {final}%.'}]}
                request = json.dumps(dict(operation=op, initial=initial, final=final, source_ids=['a']))
                self.assertEqual(checked_parse(request, 'stop', case)[1],
                                 dict(value=value, unit=unit, source_ids=['a']))

    def test_unsupported_operand(self):
        case = {'evidence': [{'chunk_id': 'a', 'text': 'Before 10%; after 20%.'}]}
        with self.assertRaisesRegex(ValueError, 'operand absent'):
            checked_parse('{"operation":"point_change","initial":10,"final":30,"source_ids":["a"]}', 'stop', case)
