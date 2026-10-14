import unittest
from unittest.mock import Mock

from src.quote_validation import generate_quote_checked


class BoundedQuoteValidationTests(unittest.TestCase):
    def test_rejected_output_is_not_returned_and_second_failure_stops(self):
        first = {'quote': 'Altered source quote.'}
        second = {'quote': 'Still not source text.'}
        invoke = Mock(side_effect=[first, second])
        validate = Mock(side_effect=ValueError('Non-member quote'))
        with self.assertRaisesRegex(ValueError, 'Non-member'):
            generate_quote_checked(invoke, 'Displayed source', validate)
        self.assertEqual(invoke.call_count, 2)
        self.assertEqual(validate.call_count, 2)
        self.assertIn('Altered source quote.', invoke.call_args.args[0])
        self.assertIn('untrusted data', invoke.call_args.args[0])
        self.assertNotIn('or repeat IDs', invoke.call_args.args[0])

    def test_provider_or_schema_failure_is_not_retried(self):
        for failure in [RuntimeError('provider'), ValueError('parse/schema')]:
            invoke = Mock(side_effect=failure)
            validate = Mock()
            with self.subTest(failure=failure), self.assertRaises(type(failure)):
                generate_quote_checked(invoke, 'Source', validate)
            self.assertEqual(invoke.call_count, 1)
            validate.assert_not_called()
