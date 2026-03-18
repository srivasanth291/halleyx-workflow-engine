import re

class WorkflowTerminationException(Exception): pass
class MaxIterationsException(Exception): pass
class RuleEngineError(Exception): pass

class RuleEngine:
    def evaluate(self, rules_queryset, input_data):
        log = []
        fallback_rule = None
        matched_rule = None

        for rule in rules_queryset.order_by('priority'):
            condition = rule.condition.strip()
            
            if condition == "DEFAULT":
                fallback_rule = rule
                log.append({
                    "rule_id": str(rule.id),
                    "priority": rule.priority,
                    "condition": condition,
                    "result": True,
                    "error": None
                })
                continue
                
            try:
                result = self._evaluate_expression(condition, input_data)
                log.append({
                    "rule_id": str(rule.id),
                    "priority": rule.priority,
                    "condition": condition,
                    "result": result,
                    "error": None
                })
                if result:
                    matched_rule = rule
                    break
            except Exception as e:
                log.append({
                    "rule_id": str(rule.id),
                    "priority": rule.priority,
                    "condition": condition,
                    "result": False,
                    "error": str(e)
                })

        final_rule = matched_rule if matched_rule else fallback_rule

        if not final_rule:
            raise WorkflowTerminationException("No conditions matched and no DEFAULT found.")

        return {
            "matched": True,
            "matched_rule_id": str(final_rule.id),
            "matched_condition": final_rule.condition,
            "next_step_id": str(final_rule.next_step_id) if final_rule.next_step_id else None,
            "evaluation_log": log
        }

    def validate_condition(self, condition_string):
        if not condition_string:
            return {"valid": False, "error": "Condition string empty"}
        cond = condition_string.strip()
        if cond == "DEFAULT":
            return {"valid": True, "error": None}
        try:
            self._validate_expression(cond)
            return {"valid": True, "error": None}
        except Exception as e:
            return {"valid": False, "error": str(e)}

    def _split_by_operator(self, expr, operator):
        parts = []
        current = ""
        in_quotes = False
        quote_char = None
        i = 0
        while i < len(expr):
            char = expr[i]
            if char in ["'", '"'] and (i == 0 or expr[i-1] != '\\'):
                if not in_quotes:
                    in_quotes = True
                    quote_char = char
                elif quote_char == char:
                    in_quotes = False
                    quote_char = None
            elif not in_quotes and expr[i:i+len(operator)] == operator:
                parts.append(current)
                current = ""
                i += len(operator)
                continue
            current += char
            i += 1
        parts.append(current)
        return parts

    def _validate_expression(self, expr):
        parts = self._split_by_operator(expr, '||')
        if not parts: raise Exception("Invalid expression")
        for part in parts:
            self._validate_and_expression(part)

    def _validate_and_expression(self, expr):
        parts = self._split_by_operator(expr, '&&')
        if not parts: raise Exception("Invalid AND expression")
        for part in parts:
            self._validate_single_token(part)

    def _validate_single_token(self, token):
        token = token.strip()
        if not token:
            raise Exception("Empty token")
            
        if token.startswith('contains(') and token.endswith(')'): return
        if token.startswith('startsWith(') and token.endswith(')'): return
        if token.startswith('endsWith(') and token.endswith(')'): return

        ops = ['==', '!=', '>=', '<=', '>', '<']
        if any(op in token for op in ops):
            return
            
        raise Exception(f"Invalid condition syntax: {token}")

    def _evaluate_expression(self, expr, data):
        parts = self._split_by_operator(expr, '||')
        for part in parts:
            if self._evaluate_and_expression(part, data):
                return True
        return False

    def _evaluate_and_expression(self, expr, data):
        parts = self._split_by_operator(expr, '&&')
        for part in parts:
            if not self._evaluate_single_token(part, data):
                return False
        return True

    def _evaluate_single_token(self, token, data):
        token = token.strip()
        
        # Functions
        m_contains = re.match(r"contains\((.+),\s*['\"](.+?)['\"]\)", token)
        if m_contains:
            field, val = m_contains.groups()
            return val in str(data.get(field.strip(), ''))

        m_starts = re.match(r"startsWith\((.+),\s*['\"](.+?)['\"]\)", token)
        if m_starts:
            field, val = m_starts.groups()
            return str(data.get(field.strip(), '')).startswith(val)

        m_ends = re.match(r"endsWith\((.+),\s*['\"](.+?)['\"]\)", token)
        if m_ends:
            field, val = m_ends.groups()
            return str(data.get(field.strip(), '')).endswith(val)

        ops = ['==', '!=', '>=', '<=', '>', '<']
        for op in ops:
            if op in token:
                parts = token.split(op, 1)
                field = parts[0].strip()
                expected = parts[1].strip().strip("'").strip('"')
                
                if expected.lower() == 'true': expected = True
                elif expected.lower() == 'false': expected = False
                elif expected.replace('.','',1).isdigit(): 
                    expected = float(expected) if '.' in expected else int(expected)
                
                actual = data.get(field)
                if actual is None:
                    return False

                if type(expected) is int or type(expected) is float:
                    actual = float(actual)

                if op == '==': return actual == expected
                if op == '!=': return actual != expected
                if op == '>': return actual > expected
                if op == '<': return actual < expected
                if op == '>=': return actual >= expected
                if op == '<=': return actual <= expected

        return False
