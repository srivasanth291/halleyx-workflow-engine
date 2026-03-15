"""
Rule engine tests.
"""
from django.test import TestCase
from apps.engine.rule_engine import RuleEngine


class RuleEngineTest(TestCase):
    def setUp(self):
        self.engine = RuleEngine()

    def test_simple_comparison_gt(self):
        result, err = self.engine._safe_evaluate('amount > 100', {'amount': 500})
        self.assertTrue(result)
        self.assertIsNone(err)

    def test_simple_comparison_false(self):
        result, err = self.engine._safe_evaluate('amount > 100', {'amount': 50})
        self.assertFalse(result)

    def test_and_condition(self):
        result, err = self.engine._safe_evaluate(
            "amount > 100 && country == 'US'",
            {'amount': 500, 'country': 'US'}
        )
        self.assertTrue(result)

    def test_and_condition_false(self):
        result, err = self.engine._safe_evaluate(
            "amount > 100 && country == 'US'",
            {'amount': 500, 'country': 'IN'}
        )
        self.assertFalse(result)

    def test_or_condition(self):
        result, err = self.engine._safe_evaluate(
            "amount > 1000 || country == 'US'",
            {'amount': 50, 'country': 'US'}
        )
        self.assertTrue(result)

    def test_contains_function(self):
        result, err = self.engine._safe_evaluate(
            "contains(department, 'Finance')",
            {'department': 'Finance Division'}
        )
        self.assertTrue(result)

    def test_starts_with_function(self):
        result, err = self.engine._safe_evaluate(
            "startsWith(email, 'admin')",
            {'email': 'admin@company.com'}
        )
        self.assertTrue(result)

    def test_ends_with_function(self):
        result, err = self.engine._safe_evaluate(
            "endsWith(email, '@tcs.com')",
            {'email': 'user@tcs.com'}
        )
        self.assertTrue(result)

    def test_boolean_field(self):
        result, err = self.engine._safe_evaluate('approved == true', {'approved': True})
        self.assertTrue(result)

    def test_validate_valid_condition(self):
        result = self.engine.validate_condition("amount > 100 && country == 'US'")
        self.assertTrue(result['valid'])
        self.assertIsNone(result['error'])

    def test_validate_default_condition(self):
        result = self.engine.validate_condition('DEFAULT')
        self.assertTrue(result['valid'])

    def test_validate_empty_condition(self):
        result = self.engine.validate_condition('')
        self.assertFalse(result['valid'])
