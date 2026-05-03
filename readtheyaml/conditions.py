from __future__ import annotations

from copy import deepcopy
from difflib import get_close_matches
from enum import Enum
from typing import Any, Dict, Tuple

from readtheyaml.exceptions.format_error import FormatError


class AtomicOp(str, Enum):
    EQ = "eq"
    NE = "ne"
    GT = "gt"
    GE = "ge"
    LT = "lt"
    LE = "le"
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"
    IN = "in"
    NOT_IN = "not_in"


class Combinator(str, Enum):
    ALL = "all"
    ANY = "any"
    NOT = "not"


_ATOMIC_OP_ALIASES = {
    "eq": AtomicOp.EQ,
    "equal": AtomicOp.EQ,
    "equals": AtomicOp.EQ,
    "==": AtomicOp.EQ,
    "ne": AtomicOp.NE,
    "not_equal": AtomicOp.NE,
    "!=": AtomicOp.NE,
    "gt": AtomicOp.GT,
    ">": AtomicOp.GT,
    "ge": AtomicOp.GE,
    "gte": AtomicOp.GE,
    ">=": AtomicOp.GE,
    "lt": AtomicOp.LT,
    "<": AtomicOp.LT,
    "le": AtomicOp.LE,
    "lte": AtomicOp.LE,
    "<=": AtomicOp.LE,
    "exists": AtomicOp.EXISTS,
    "present": AtomicOp.EXISTS,
    "not_exists": AtomicOp.NOT_EXISTS,
    "missing": AtomicOp.NOT_EXISTS,
    "in": AtomicOp.IN,
    "not_in": AtomicOp.NOT_IN,
    "nin": AtomicOp.NOT_IN,
}

_COMBINATOR_ALIASES = {
    "all": Combinator.ALL,
    "and": Combinator.ALL,
    "any": Combinator.ANY,
    "or": Combinator.ANY,
    "not": Combinator.NOT,
}


def parse_when(condition: Any, location: str = "when") -> dict | None:
    if condition is None:
        return None
    return _parse_condition(condition, location)


def _parse_condition(condition: Any, location: str) -> dict:
    if not isinstance(condition, dict):
        raise FormatError(f"Invalid {location}: must be a mapping/dictionary.")

    keys = set(condition.keys())
    resolved_combinators = []
    for key in keys:
        combinator = _resolve_combinator(key)
        if combinator is not None:
            resolved_combinators.append((key, combinator))

    if resolved_combinators:
        if len(resolved_combinators) != 1 or len(keys) != 1:
            raise FormatError(f"Invalid {location}: combinators ('all', 'any', 'not') cannot be mixed with other keys.")

        source_key, combinator = resolved_combinators[0]
        if combinator in {Combinator.ALL, Combinator.ANY}:
            raw_children = condition[source_key]
            if not isinstance(raw_children, list) or not raw_children:
                raise FormatError(f"Invalid {location}.{source_key}: must be a non-empty list.")

            return {
                "kind": combinator,
                "conditions": [_parse_condition(child, f"{location}.{source_key}[{index}]") for index, child in enumerate(raw_children)]
            }

        return {"kind": Combinator.NOT, "condition": _parse_condition(condition[source_key], f"{location}.{source_key}")}

    _raise_if_misspelled_combinator(condition, location)

    required_atomic = {"field", "op"}
    allowed_atomic = {"field", "op", "value"}
    unknown_atomic = keys - allowed_atomic
    missing_atomic = required_atomic - keys

    if missing_atomic:
        raise FormatError(f"Invalid {location}: missing required key(s): {', '.join(sorted(missing_atomic))}.")
    if unknown_atomic:
        raise FormatError(f"Invalid {location}: unknown key(s): {', '.join(sorted(unknown_atomic))}.")

    field_path = condition["field"]
    op = condition["op"]

    if not isinstance(field_path, str) or not field_path.strip():
        raise FormatError(f"Invalid {location}.field: must be a non-empty string.")
    if any(not segment for segment in field_path.split(".")):
        raise FormatError(f"Invalid {location}.field: contains an empty path segment.")
    parsed_op = _resolve_atomic_op(op, f"{location}.op")

    has_value = "value" in condition
    if parsed_op in {AtomicOp.EXISTS, AtomicOp.NOT_EXISTS} and has_value:
        raise FormatError(f"Invalid {location}: operator '{parsed_op.value}' does not accept 'value'.")
    if parsed_op not in {AtomicOp.EXISTS, AtomicOp.NOT_EXISTS} and not has_value:
        raise FormatError(f"Invalid {location}: operator '{parsed_op.value}' requires 'value'.")
    if parsed_op in {AtomicOp.IN, AtomicOp.NOT_IN} and has_value:
        haystack = condition["value"]
        if not isinstance(haystack, (list, tuple, set, frozenset)):
            raise FormatError(f"Invalid {location}.value: operator '{parsed_op.value}' expects a list/tuple/set.")

    parsed = {"kind": "atomic", "field": field_path, "op": parsed_op}
    if has_value:
        parsed["value"] = deepcopy(condition["value"])
    return parsed


def evaluate_when(condition: dict | None, context: Dict[str, Any]) -> bool:
    if condition is None:
        return True

    kind = condition["kind"]
    if kind == Combinator.ALL:
        return all(evaluate_when(child, context) for child in condition["conditions"])
    if kind == Combinator.ANY:
        return any(evaluate_when(child, context) for child in condition["conditions"])
    if kind == Combinator.NOT:
        return not evaluate_when(condition["condition"], context)

    field_exists, field_value = _resolve_path(context, condition["field"])
    op = condition["op"]

    if op == AtomicOp.EXISTS:
        return field_exists
    if op == AtomicOp.NOT_EXISTS:
        return not field_exists
    if not field_exists:
        return False

    target = condition["value"]
    if op == AtomicOp.EQ:
        return field_value == target
    if op == AtomicOp.NE:
        return field_value != target
    if op in {AtomicOp.GT, AtomicOp.GE, AtomicOp.LT, AtomicOp.LE}:
        return _safe_cmp(field_value, target, op)
    if op == AtomicOp.IN:
        return _safe_membership(field_value, target)
    if op == AtomicOp.NOT_IN:
        return not _safe_membership(field_value, target)

    return False


def format_when_human(condition: dict | None) -> str:
    if condition is None:
        return ""

    kind = condition["kind"]
    if kind == Combinator.ALL:
        children = [format_when_human(child) for child in condition["conditions"]]
        return "all of: " + "; ".join(children)
    if kind == Combinator.ANY:
        children = [format_when_human(child) for child in condition["conditions"]]
        return "any of: " + "; ".join(children)
    if kind == Combinator.NOT:
        return "not (" + format_when_human(condition["condition"]) + ")"

    field = condition["field"]
    op = condition["op"]

    if op == AtomicOp.EXISTS:
        return f"'{field}' exists"
    if op == AtomicOp.NOT_EXISTS:
        return f"'{field}' is missing"

    value = condition.get("value")
    if op == AtomicOp.EQ:
        return f"'{field}' is {_format_when_value(value)}"
    if op == AtomicOp.NE:
        return f"'{field}' is not {_format_when_value(value)}"
    if op == AtomicOp.GT:
        return f"'{field}' is greater than {_format_when_value(value)}"
    if op == AtomicOp.GE:
        return f"'{field}' is at least {_format_when_value(value)}"
    if op == AtomicOp.LT:
        return f"'{field}' is less than {_format_when_value(value)}"
    if op == AtomicOp.LE:
        return f"'{field}' is at most {_format_when_value(value)}"
    if op == AtomicOp.IN:
        return f"'{field}' is one of {_format_when_value(value)}"
    if op == AtomicOp.NOT_IN:
        return f"'{field}' is not one of {_format_when_value(value)}"

    return str(condition)


def _resolve_path(data: Dict[str, Any], field_path: str) -> Tuple[bool, Any]:
    current: Any = data
    for segment in field_path.split("."):
        if not isinstance(current, dict) or segment not in current:
            return False, None
        current = current[segment]
    return True, current


def _safe_cmp(left: Any, right: Any, op: AtomicOp) -> bool:
    try:
        if op == AtomicOp.GT:
            return left > right
        if op == AtomicOp.GE:
            return left >= right
        if op == AtomicOp.LT:
            return left < right
        if op == AtomicOp.LE:
            return left <= right
        return False
    except TypeError:
        return False


def _safe_membership(needle: Any, haystack: Any) -> bool:
    try:
        return needle in haystack
    except TypeError:
        return False


def _format_when_value(value: Any) -> str:
    if isinstance(value, str):
        return f"'{value}'"
    if isinstance(value, (list, tuple, set, frozenset)):
        return "[" + ", ".join(_format_when_value(v) for v in value) + "]"
    return str(value)


def _normalize_token(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def _resolve_combinator(value: Any) -> Combinator | None:
    if not isinstance(value, str):
        return None
    return _COMBINATOR_ALIASES.get(_normalize_token(value))


def _resolve_atomic_op(value: Any, location: str) -> AtomicOp:
    if not isinstance(value, str):
        raise FormatError(f"Invalid {location}: unsupported operator '{value}'.")

    token = _normalize_token(value)
    op = _ATOMIC_OP_ALIASES.get(token)
    if op is not None:
        return op

    canonical = sorted(op.value for op in AtomicOp)
    suggestions = get_close_matches(token, sorted(_ATOMIC_OP_ALIASES), n=3, cutoff=0.6)
    suggestion_text = ""
    if suggestions:
        suggestion_text = f" Did you mean: {', '.join(suggestions)}?"

    raise FormatError(f"Invalid {location}: unsupported operator '{value}'. Supported operators: {', '.join(canonical)}.{suggestion_text}")


def _raise_if_misspelled_combinator(condition: dict, location: str) -> None:
    if len(condition) != 1:
        return

    key = next(iter(condition.keys()))
    if not isinstance(key, str):
        return

    normalized = _normalize_token(key)
    if normalized in {"field", "op", "value"} or normalized in _COMBINATOR_ALIASES:
        return

    suggestions = get_close_matches(normalized, sorted(_COMBINATOR_ALIASES), n=2, cutoff=0.6)
    if suggestions:
        raise FormatError(f"Invalid {location}: unknown combinator key '{key}'. Did you mean: {', '.join(suggestions)}?")
