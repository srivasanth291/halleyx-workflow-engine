"""
Custom safe rule engine — NO eval(), NO exec().
Evaluates workflow transition conditions using a hand-built tokenizer and parser.
"""
import re
import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class WorkflowTerminationException(Exception):
    """Raised when no rule matches and no DEFAULT rule exists."""
    pass


class MaxIterationsException(Exception):
    """Raised when execution exceeds max_iterations — loop detected."""
    pass


class RuleEngineError(Exception):
    """Raised when a condition cannot be parsed."""
    pass


class RuleEngine:
    """
    Safe rule engine that evaluates workflow transition conditions.

    NEVER uses Python eval() or exec().
    All parsing is done by a custom tokenizer.

    Supported operators:
        Comparison : == != > < >= <=
        Logical    : && (AND)  || (OR)
        String     : contains(field, "value")
                     startsWith(field, "prefix")
                     endsWith(field, "suffix")
        Special    : DEFAULT — always matches, used as fallback
    """

    COMPARISON_OPERATORS = ('==', '!=', '>=', '<=', '>', '<')
    STRING_FUNCTIONS = ('contains', 'startsWith', 'endsWith')

    # ─────────────────────────────────────────────────────
    # PUBLIC API
    # ─────────────────────────────────────────────────────

    def evaluate(self, rules_queryset, input_data: Dict[str, Any]) -> Dict:
        """
        Evaluate rules in priority order against input_data.

        Returns:
            {
                "matched": bool,
                "matched_rule_id": str or None,
                "matched_condition": str or None,
                "next_step_id": str or None,
                "evaluation_log": [...]
            }
        """
        evaluation_log = []
        default_rule = None

        for rule in rules_queryset:
            condition = rule.condition.strip()

            # Save DEFAULT rule as fallback, skip now
            if condition.upper() == 'DEFAULT':
                default_rule = rule
                evaluation_log.append({
                    'rule_id': str(rule.id),
                    'priority': rule.priority,
                    'condition': condition,
                    'result': 'DEFAULT (pending)',
                    'error': None,
                })
                continue

            # Try evaluating the condition
            result, error = self._safe_evaluate(condition, input_data)
            evaluation_log.append({
                'rule_id': str(rule.id),
                'priority': rule.priority,
                'condition': condition,
                'result': result,
                'error': error,
            })

            if error:
                logger.warning(
                    'Rule %s condition "%s" failed to evaluate: %s',
                    rule.id, condition, error
                )
                continue

            if result is True:
                # Update the DEFAULT entry in log to "skipped"
                for entry in evaluation_log:
                    if entry.get('result') == 'DEFAULT (pending)':
                        entry['result'] = False
                return {
                    'matched': True,
                    'matched_rule_id': str(rule.id),
                    'matched_condition': condition,
                    'next_step_id': str(rule.next_step_id) if rule.next_step_id else None,
                    'evaluation_log': evaluation_log,
                }

        # No non-DEFAULT rule matched — try DEFAULT fallback
        if default_rule is not None:
            for entry in evaluation_log:
                if entry.get('result') == 'DEFAULT (pending)':
                    entry['result'] = True
            return {
                'matched': True,
                'matched_rule_id': str(default_rule.id),
                'matched_condition': 'DEFAULT',
                'next_step_id': str(default_rule.next_step_id) if default_rule.next_step_id else None,
                'evaluation_log': evaluation_log,
            }

        # No match at all
        raise WorkflowTerminationException(
            'No rule matched the current execution data and no DEFAULT rule found.'
        )

    def validate_condition(self, condition: str) -> Dict:
        """
        Validate condition syntax without evaluating against real data.

        Returns:
            {"valid": True, "error": None}
            or
            {"valid": False, "error": "description"}
        """
        condition = condition.strip()
        if not condition:
            return {'valid': False, 'error': 'Condition cannot be empty.'}

        if condition.upper() == 'DEFAULT':
            return {'valid': True, 'error': None}

        # Use dummy data for syntax validation
        dummy_data = {}
        try:
            tokens = self._split_logical(condition)
            for token in tokens:
                token = token.strip()
                if not token:
                    continue
                # Try to parse token structure
                self._parse_token_structure(token)
            return {'valid': True, 'error': None}
        except RuleEngineError as exc:
            return {'valid': False, 'error': str(exc)}
        except Exception as exc:
            return {'valid': False, 'error': f'Unexpected parse error: {exc}'}

    # ─────────────────────────────────────────────────────
    # PRIVATE: SAFE EVALUATION
    # ─────────────────────────────────────────────────────

    def _safe_evaluate(self, condition: str, data: Dict) -> Tuple[Optional[bool], Optional[str]]:
        """
        Safely evaluate a condition string against data dict.
        Returns (result: bool | None, error: str | None).
        """
        try:
            result = self._evaluate_expression(condition.strip(), data)
            return result, None
        except RuleEngineError as exc:
            return None, str(exc)
        except KeyError as exc:
            return None, f'Field not found in data: {exc}'
        except Exception as exc:
            return None, f'Evaluation error: {exc}'

    def _evaluate_expression(self, expression: str, data: Dict) -> bool:
        """
        Evaluate a complex expression with && and || operators.
        Handles operator precedence: && binds tighter than ||.
        """
        expression = expression.strip()

        # Split by || first (lowest precedence)
        or_parts = self._split_by_operator(expression, '||')
        if len(or_parts) > 1:
            return any(self._evaluate_and_expression(part.strip(), data) for part in or_parts)

        return self._evaluate_and_expression(expression, data)

    def _evaluate_and_expression(self, expression: str, data: Dict) -> bool:
        """Evaluate a chain of && conditions."""
        and_parts = self._split_by_operator(expression, '&&')
        return all(self._evaluate_single_token(part.strip(), data) for part in and_parts)

    def _evaluate_single_token(self, token: str, data: Dict) -> bool:
        """Evaluate a single atomic condition token."""
        token = token.strip()

        # Remove outer parentheses if present
        if token.startswith('(') and token.endswith(')'):
            token = token[1:-1].strip()

        # Check for string function calls
        func_match = re.match(
            r'^(contains|startsWith|endsWith)\s*\(\s*(\w+)\s*,\s*["\'](.+?)["\']\s*\)$',
            token, re.IGNORECASE
        )
        if func_match:
            func_name = func_match.group(1)
            field = func_match.group(2)
            value = func_match.group(3)
            return self._apply_string_function(func_name, field, value, data)

        # Parse comparison: field operator value
        return self._evaluate_comparison(token, data)

    def _evaluate_comparison(self, token: str, data: Dict) -> bool:
        """Parse and evaluate a comparison expression: field op value."""
        field, operator, raw_value = self._parse_comparison_token(token)

        # Get field value from data
        if field not in data:
            raise RuleEngineError(f"Field '{field}' not found in execution data.")

        field_value = data[field]
        expected_value = self._coerce_value(raw_value, field_value)

        return self._apply_operator(field_value, operator, expected_value)

    def _apply_operator(self, field_value: Any, operator: str, expected_value: Any) -> bool:
        """Apply a comparison operator safely."""
        try:
            # Numeric comparison
            if isinstance(field_value, (int, float)) or isinstance(expected_value, (int, float)):
                fv = float(field_value) if not isinstance(field_value, bool) else field_value
                ev = float(expected_value) if not isinstance(expected_value, bool) else expected_value
                ops = {
                    '==': fv == ev, '!=': fv != ev,
                    '>': fv > ev, '<': fv < ev,
                    '>=': fv >= ev, '<=': fv <= ev,
                }
                return ops[operator]

            # Boolean comparison
            if isinstance(field_value, bool) or isinstance(expected_value, bool):
                ops = {'==': field_value == expected_value, '!=': field_value != expected_value}
                return ops.get(operator, False)

            # String comparison
            fv = str(field_value)
            ev = str(expected_value)
            ops = {
                '==': fv == ev, '!=': fv != ev,
                '>': fv > ev, '<': fv < ev,
                '>=': fv >= ev, '<=': fv <= ev,
            }
            return ops[operator]
        except (TypeError, ValueError) as exc:
            raise RuleEngineError(f'Cannot apply operator {operator}: {exc}')

    def _apply_string_function(self, func: str, field: str, value: str, data: Dict) -> bool:
        """Apply a string function: contains, startsWith, endsWith."""
        if field not in data:
            raise RuleEngineError(f"Field '{field}' not found in execution data.")
        field_val = str(data[field])
        if func == 'contains':
            return value in field_val
        elif func == 'startsWith':
            return field_val.startswith(value)
        elif func == 'endsWith':
            return field_val.endswith(value)
        raise RuleEngineError(f"Unknown string function: {func}")

    # ─────────────────────────────────────────────────────
    # PRIVATE: PARSING UTILITIES
    # ─────────────────────────────────────────────────────

    def _split_by_operator(self, expression: str, operator: str) -> List[str]:
        """
        Split expression by a logical operator (|| or &&),
        respecting quoted strings and parentheses.
        """
        parts = []
        depth = 0
        in_single_quote = False
        in_double_quote = False
        current = []
        i = 0
        op_len = len(operator)

        while i < len(expression):
            ch = expression[i]

            if ch == "'" and not in_double_quote:
                in_single_quote = not in_single_quote
                current.append(ch)
                i += 1
                continue

            if ch == '"' and not in_single_quote:
                in_double_quote = not in_double_quote
                current.append(ch)
                i += 1
                continue

            if in_single_quote or in_double_quote:
                current.append(ch)
                i += 1
                continue

            if ch == '(':
                depth += 1
                current.append(ch)
                i += 1
                continue

            if ch == ')':
                depth -= 1
                current.append(ch)
                i += 1
                continue

            if depth == 0 and expression[i:i + op_len] == operator:
                parts.append(''.join(current).strip())
                current = []
                i += op_len
                continue

            current.append(ch)
            i += 1

        if current:
            parts.append(''.join(current).strip())

        return parts if len(parts) > 1 else [expression]

    def _split_logical(self, expression: str) -> List[str]:
        """Split by both && and || for validation purposes."""
        parts = self._split_by_operator(expression, '||')
        result = []
        for part in parts:
            result.extend(self._split_by_operator(part, '&&'))
        return result

    def _parse_comparison_token(self, token: str) -> Tuple[str, str, str]:
        """
        Parse a comparison token into (field, operator, value).
        Example: "amount > 100" → ("amount", ">", "100")
        """
        # Try matching operators from longest to shortest to avoid ambiguity
        for op in ('>=', '<=', '!=', '==', '>', '<'):
            idx = token.find(op)
            if idx > 0:
                field = token[:idx].strip()
                raw_value = token[idx + len(op):].strip()
                # Validate field name
                if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_.]*$', field):
                    raise RuleEngineError(f"Invalid field name: '{field}'")
                if not field or not raw_value:
                    raise RuleEngineError(f"Malformed condition: '{token}'")
                return field, op, raw_value

        raise RuleEngineError(
            f"No valid comparison operator found in: '{token}'. "
            f"Supported: {', '.join(self.COMPARISON_OPERATORS)}"
        )

    def _parse_token_structure(self, token: str) -> None:
        """Parse token structure for validation (no actual evaluation)."""
        token = token.strip()
        if not token:
            return

        # Check for string functions
        func_match = re.match(
            r'^(contains|startsWith|endsWith)\s*\(\s*(\w+)\s*,\s*["\'](.+?)["\']\s*\)$',
            token, re.IGNORECASE
        )
        if func_match:
            return  # Valid function call

        # Must be a comparison
        self._parse_comparison_token(token)

    def _coerce_value(self, raw_value: str, field_value: Any) -> Any:
        """
        Coerce a raw string value from condition to the appropriate Python type.
        Matches the type of the field value when possible.
        """
        raw_value = raw_value.strip()

        # Remove surrounding quotes for strings
        if (raw_value.startswith("'") and raw_value.endswith("'")) or \
           (raw_value.startswith('"') and raw_value.endswith('"')):
            return raw_value[1:-1]

        # Boolean literals
        if raw_value.lower() == 'true':
            return True
        if raw_value.lower() == 'false':
            return False

        # Null/None
        if raw_value.lower() in ('null', 'none'):
            return None

        # Numeric
        try:
            if '.' in raw_value:
                return float(raw_value)
            return int(raw_value)
        except ValueError:
            pass

        # Return as string
        return raw_value
