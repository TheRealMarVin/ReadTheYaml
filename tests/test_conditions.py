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


@pytest.mark.parametrize(
    ("condition", "message"),
    [
        ({"field": "a", "op": "eq"}, "operator 'eq' requires 'value'"),
        ({"field": "a", "op": "exists", "value": 1}, "operator 'exists' does not accept 'value'"),
        ({"field": "", "op": "exists"}, "must be a non-empty string"),
        ({"field": "a..b", "op": "exists"}, "contains an empty path segment"),
        ({"field": "a", "op": 5, "value": 1}, "unsupported operator '5'"),
        ({"field": "a", "op": "in", "value": "abc"}, "expects a list/tuple/set"),
    ],
)
def test_parse_when_invalid_shape_error_message_is_specific(condition, message):
    with pytest.raises(FormatError, match=message):
        parse_when(condition)


def test_parse_when_rejects_non_mapping_condition_with_clear_error():
    with pytest.raises(FormatError, match="must be a mapping/dictionary"):
        parse_when(["not", "a", "mapping"])


def test_parse_when_rejects_mixed_combinator_and_atomic_keys_with_clear_error():
    with pytest.raises(FormatError, match="combinators \\('all', 'any', 'not'\\) cannot be mixed with other keys"):
        parse_when({"all": [{"field": "a", "op": "exists"}], "field": "a"})


@pytest.mark.parametrize(
    ("raw_op", "expected"),
    [
        ("present", AtomicOp.EXISTS),
        ("missing", AtomicOp.NOT_EXISTS),
        ("!=", AtomicOp.NE),
        ("<=", AtomicOp.LE),
        ("nin", AtomicOp.NOT_IN),
    ],
)
def test_parse_when_operator_aliases_are_mapped(raw_op, expected):
    condition = {"field": "a", "op": raw_op}
    if expected not in {AtomicOp.EXISTS, AtomicOp.NOT_EXISTS}:
        condition["value"] = [1, 2] if expected in {AtomicOp.IN, AtomicOp.NOT_IN} else 1

    parsed = parse_when(condition)
    assert parsed["op"] == expected


def test_parse_when_normalizes_case_space_and_dash_for_operators_and_combinators():
    parsed = parse_when({"field": "a", "op": "NOT EXISTS"})
    assert parsed["op"] == AtomicOp.NOT_EXISTS

    parsed_combinator = parse_when({"AnD": [{"field": "a", "op": "exists"}]})
    assert parsed_combinator["kind"] == Combinator.ALL


def test_parse_when_with_none_returns_none():
    assert parse_when(None) is None


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


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [
        (4, 3, True),
        (3, 3, False),
        (3.1, 3, True),
        ("b", "a", True),
        ("a", "b", False),
        ("10", 2, False),
        (1, "2", False),
    ],
)
def test_evaluate_when_gt_matrix(left, right, expected):
    context = {"a": left}
    assert evaluate_when(parse_when({"field": "a", "op": "gt", "value": right}), context) is expected


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [
        (3, 3.0, True),
        (3.0, 3.0, True),
        (3.0000001, 3.0, False),
        ("3", 3, False),
        (3, "3", False),
        (True, 1, True),
        (False, 0, True),
    ],
)
def test_evaluate_when_eq_matrix_includes_numeric_and_cross_type_cases(left, right, expected):
    context = {"a": left}
    assert evaluate_when(parse_when({"field": "a", "op": "eq", "value": right}), context) is expected


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [
        (3, 3.0, False),
        (3.0, 3.0, False),
        ("3", 3, True),
        (3, "3", True),
        (True, 1, False),
        (False, 0, False),
    ],
)
def test_evaluate_when_ne_matrix_includes_numeric_and_cross_type_cases(left, right, expected):
    context = {"a": left}
    assert evaluate_when(parse_when({"field": "a", "op": "ne", "value": right}), context) is expected


def test_evaluate_when_no_epsilon_for_float_eq():
    context = {"a": 0.1 + 0.2}
    assert evaluate_when(parse_when({"field": "a", "op": "eq", "value": 0.3}), context) is False


def test_evaluate_when_in_and_not_in_with_mixed_value_types():
    context = {"a": 1, "b": "1", "mode": "fast"}

    assert evaluate_when(parse_when({"field": "a", "op": "in", "value": [1, 2, 3]}), context) is True
    assert evaluate_when(parse_when({"field": "b", "op": "in", "value": [1, 2, 3]}), context) is False
    assert evaluate_when(parse_when({"field": "mode", "op": "not_in", "value": ["safe", "slow"]}), context) is True


def test_evaluate_when_exists_and_not_exists_for_nested_object_member_paths():
    context = {"A": {"X": 4}}

    assert evaluate_when(parse_when({"field": "A.X", "op": "exists"}), context) is True
    assert evaluate_when(parse_when({"field": "A.Y", "op": "not_exists"}), context) is True


def test_evaluate_when_path_traversal_stops_when_intermediate_is_not_mapping():
    context = {"A": 4}
    assert evaluate_when(parse_when({"field": "A.X", "op": "exists"}), context) is False
    assert evaluate_when(parse_when({"field": "A.X", "op": "eq", "value": 4}), context) is False


def test_evaluate_when_returns_true_when_condition_is_none():
    assert evaluate_when(None, {"a": 1}) is True


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


def test_evaluate_when_string_greater_than_string_is_supported_by_python_ordering():
    context = {"a": "zebra"}
    assert evaluate_when(parse_when({"field": "a", "op": "gt", "value": "apple"}), context) is True


def test_evaluate_when_cascading_conditions_transitive_activation():
    context = {
        "network": {"port": 8080},
        "high_port_mode": True,
    }
    parent_condition = parse_when({"field": "network.port", "op": "gt", "value": 128})
    child_condition = parse_when({"field": "high_port_mode", "op": "eq", "value": True})

    assert evaluate_when(parent_condition, context) is True
    assert evaluate_when(child_condition, context) is True


def test_evaluate_when_cascading_conditions_downstream_inactive_when_parent_source_missing():
    context = {}
    parent_condition = parse_when({"field": "network.port", "op": "gt", "value": 128})
    child_condition = parse_when({"field": "high_port_mode", "op": "eq", "value": True})

    assert evaluate_when(parent_condition, context) is False
    assert evaluate_when(child_condition, context) is False


def test_evaluate_when_cascading_conditions_downstream_inactive_when_parent_value_false():
    context = {
        "network": {"port": 8080},
        "high_port_mode": False,
    }
    parent_condition = parse_when({"field": "network.port", "op": "gt", "value": 128})
    child_condition = parse_when({"field": "high_port_mode", "op": "eq", "value": True})

    assert evaluate_when(parent_condition, context) is True
    assert evaluate_when(child_condition, context) is False
