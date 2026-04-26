import pytest

from readtheyaml.conditions import AtomicOp, Combinator, evaluate_when, parse_when
from readtheyaml.exceptions.format_error import FormatError


def test_parse_when_atomic_eq():
    parsed = parse_when({"field": "flags.compile_enabled", "op": "eq", "value": True})

    assert parsed == {
        "kind": "atomic",
        "field": "flags.compile_enabled",
        "op": AtomicOp.EQ,
        "value": True,
    }


def test_parse_when_all_any_not_tree():
    parsed = parse_when(
        {
            "all": [
                {"field": "a", "op": "exists"},
                {"not": {"field": "mode", "op": "in", "value": ["dry-run", "disabled"]}},
            ]
        }
    )

    assert parsed["kind"] == Combinator.ALL
    assert len(parsed["conditions"]) == 2
    assert parsed["conditions"][1]["kind"] == Combinator.NOT


def test_parse_when_supports_aliases_and_symbols():
    parsed = parse_when({"field": "flags.compile_enabled", "op": "equal", "value": True})
    assert parsed["op"] == AtomicOp.EQ

    parsed_symbol = parse_when({"field": "count", "op": ">=", "value": 2})
    assert parsed_symbol["op"] == AtomicOp.GE

    parsed_combinator = parse_when({"and": [{"field": "a", "op": "exists"}]})
    assert parsed_combinator["kind"] == Combinator.ALL


@pytest.mark.parametrize(
    "condition",
    [
        {"field": "a", "op": "eq"},
        {"field": "a", "op": "exists", "value": 1},
        {"field": "a", "op": "in", "value": "abc"},
        {"all": []},
        {"all": [{"field": "a", "op": "exists"}], "field": "a"},
        {"field": "a..b", "op": "exists"},
    ],
)
def test_parse_when_rejects_invalid_shapes(condition):
    with pytest.raises(FormatError):
        parse_when(condition)


def test_parse_when_invalid_operator_has_suggestion():
    with pytest.raises(FormatError, match="Did you mean"):
        parse_when({"field": "a", "op": "eqaul", "value": 1})


def test_parse_when_misspelled_combinator_is_rejected():
    with pytest.raises(FormatError, match="unknown combinator key 'aal'.*Did you mean: all"):
        parse_when({"aal": [{"field": "a", "op": "exists"}]})


def test_parse_when_rejects_unknown_keys_in_atomic_condition():
    with pytest.raises(FormatError, match="unknown key\\(s\\): extra"):
        parse_when({"field": "a", "op": "eq", "value": 1, "extra": 2})


def test_parse_when_rejects_not_in_with_non_collection_value():
    with pytest.raises(FormatError, match="expects a list/tuple/set"):
        parse_when({"field": "a", "op": "not_in", "value": "abc"})


def test_evaluate_when_atomic_operators():
    context = {
        "enabled": True,
        "threshold": 5,
        "mode": "fast",
        "items": {"nested": {"value": 7}},
    }

    assert evaluate_when(parse_when({"field": "enabled", "op": "eq", "value": True}), context) is True
    assert evaluate_when(parse_when({"field": "threshold", "op": "gt", "value": 3}), context) is True
    assert evaluate_when(parse_when({"field": "threshold", "op": "lt", "value": 3}), context) is False
    assert evaluate_when(parse_when({"field": "items.nested.value", "op": "exists"}), context) is True
    assert evaluate_when(parse_when({"field": "items.nested.missing", "op": "not_exists"}), context) is True
    assert evaluate_when(parse_when({"field": "mode", "op": "in", "value": ["safe", "fast"]}), context) is True
    assert evaluate_when(parse_when({"field": "mode", "op": "not_in", "value": ["safe"]}), context) is True


def test_evaluate_when_missing_path_is_false_for_non_existence_ops():
    context = {"a": 1}

    assert evaluate_when(parse_when({"field": "missing", "op": "eq", "value": 1}), context) is False
    assert evaluate_when(parse_when({"field": "missing", "op": "gt", "value": 1}), context) is False


def test_evaluate_when_not_combinator_over_non_boolean_field_result():
    context = {"count": 0}
    condition = parse_when({"not": {"field": "count", "op": "eq", "value": 1}})

    assert evaluate_when(condition, context) is True


def test_evaluate_when_ordered_comparison_cross_type_returns_false():
    context = {"a": "hello", "b": True}

    assert evaluate_when(parse_when({"field": "a", "op": "ge", "value": True}), context) is False
    assert evaluate_when(parse_when({"field": "b", "op": "lt", "value": "z"}), context) is False


def test_evaluate_when_nested_combinators_mixed_paths_and_ops():
    context = {
        "mode": "prod",
        "compile_enabled": True,
        "threads": 4,
        "flags": {"beta": False},
    }
    condition = parse_when(
        {
            "all": [
                {"field": "compile_enabled", "op": "eq", "value": True},
                {
                    "any": [
                        {"field": "mode", "op": "in", "value": ["prod", "stage"]},
                        {"field": "threads", "op": "ge", "value": 8},
                    ]
                },
                {
                    "not": {
                        "field": "flags.beta",
                        "op": "eq",
                        "value": True,
                    }
                },
            ]
        }
    )

    assert evaluate_when(condition, context) is True


def test_evaluate_when_nested_combinators_short_circuit_to_false():
    context = {
        "mode": "dev",
        "compile_enabled": True,
        "threads": 2,
        "flags": {"beta": True},
    }
    condition = parse_when(
        {
            "all": [
                {"field": "compile_enabled", "op": "eq", "value": True},
                {
                    "any": [
                        {"field": "mode", "op": "in", "value": ["prod", "stage"]},
                        {"field": "threads", "op": "ge", "value": 8},
                    ]
                },
                {
                    "not": {
                        "field": "flags.beta",
                        "op": "eq",
                        "value": True,
                    }
                },
            ]
        }
    )

    assert evaluate_when(condition, context) is False
