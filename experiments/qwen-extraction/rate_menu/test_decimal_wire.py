import json
import unittest
from decimal_wire import checked_parse

class Wire(unittest.TestCase):
    case = dict(evidence=[dict(chunk_id='a', text='Before 6.4%, after 8%. Elsewhere 0%.')])
    def check(self, initial, final='8', ids='["a"]', extra=''):
        return checked_parse('{"operation":"relative_change","initial":'+initial+',"final":'+final+',"source_ids":'+ids+extra+'}', 'stop', self.case)
    def test_decimal_number_and_string_equivalent(self):
        a = self.check('6.4')
        self.assertEqual(a, self.check('"6.4"', '"8"'))
        self.assertEqual(a[1]['unit'], '%')
    def test_invalid_requests(self):
        for a,b,ids,extra in [('0','8','["a"]',''),('true','8','["a"]',''),('6.4e0','8','["a"]',''),('NaN','8','["a"]',''),('6.4000000000000','8','["a"]',''),('6.4','8','[1]',''),('6.4','8','["a"]',',"initial":6.4')]:
            with self.subTest(a=a,ids=ids,extra=extra), self.assertRaises(ValueError):
                self.check(a,b,ids,extra)
