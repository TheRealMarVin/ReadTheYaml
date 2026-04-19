import pytest

from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.schema import Schema


def _required_int_schema_yaml() -> str:
    return """
        count:
          type: int
          description: Item count
          required: true
    """


def _optional_int_schema_yaml(default_literal: str) -> str:
    return f"""
        count:
          type: int
          description: Item count
          required: false
          default: {default_literal}
    """


def _required_float_schema_yaml() -> str:
    return """
        ratio:
          type: float
          description: Ratio value
          required: true
    """


def _optional_float_schema_yaml(default_literal: str) -> str:
    return f"""
        ratio:
          type: float
          description: Ratio value
          required: false
          default: {default_literal}
    """


def test_int_required_accepts_integer(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _required_int_schema_yaml(), "config.yaml": "count: 42"}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["count"] == 42
    assert data_with_default["count"] == 42


def test_int_required_accepts_numeric_string_and_keeps_raw_config(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _required_int_schema_yaml(), "config.yaml": 'count: "42"'}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["count"] == 42
    assert data_with_default["count"] == "42"


def test_int_required_rejects_fractional_float(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _required_int_schema_yaml(), "config.yaml": "count: 3.5"}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    with pytest.raises(ValidationError, match="not of type of the field"):
        schema.validate_file(files["config.yaml"])


def test_int_required_rejects_bool_literal(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _required_int_schema_yaml(), "config.yaml": "count: true"}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    with pytest.raises(ValidationError, match="contains True or False"):
        schema.validate_file(files["config.yaml"])


def test_int_required_missing_field_rejected(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _required_int_schema_yaml(), "config.yaml": "{}"}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    with pytest.raises(ValidationError, match="Missing required field 'count'"):
        schema.validate_file(files["config.yaml"])


def test_int_optional_missing_field_uses_default(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _optional_int_schema_yaml("7"), "config.yaml": "{}"}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["count"] == 7
    assert data_with_default["count"] == 7


def test_int_optional_provided_value_overrides_default(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _optional_int_schema_yaml("7"), "config.yaml": "count: 3"}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["count"] == 3
    assert data_with_default["count"] == 3


def test_int_optional_without_default_rejected(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": """
                count:
                  type: int
                  description: Item count
                  required: false
            """,
            "config.yaml": "{}",
        }
    )

    with pytest.raises(ValidationError, match="invalid default value"):
        Schema.from_yaml(str(files["schema.yaml"]))


def test_int_with_value_range_accepts_in_bounds_value(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": """
                count:
                  type: int
                  description: Item count
                  required: true
                  value_range: [1, 10]
            """,
            "config.yaml": "count: 10",
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, _ = schema.validate_file(files["config.yaml"])
    assert built["count"] == 10


def test_int_with_value_range_rejects_out_of_bounds_value(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": """
                count:
                  type: int
                  description: Item count
                  required: true
                  value_range: [1, 10]
            """,
            "config.yaml": "count: 11",
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    with pytest.raises(ValidationError, match="Value must be at most 10"):
        schema.validate_file(files["config.yaml"])


def test_int_schema_with_invalid_range_length_rejected(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": """
                count:
                  type: int
                  description: Item count
                  required: true
                  value_range: [1]
            """,
            "config.yaml": "count: 1",
        }
    )

    with pytest.raises(ValidationError, match="Range must have 2 values, 1 provided"):
        Schema.from_yaml(str(files["schema.yaml"]))


def test_float_required_accepts_float(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _required_float_schema_yaml(), "config.yaml": "ratio: 0.75"}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["ratio"] == 0.75
    assert data_with_default["ratio"] == 0.75


def test_float_required_accepts_scientific_notation_string(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _required_float_schema_yaml(), "config.yaml": 'ratio: "1e-2"'}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["ratio"] == 0.01
    assert data_with_default["ratio"] == "1e-2"


def test_float_required_rejects_bool_literal(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _required_float_schema_yaml(), "config.yaml": "ratio: false"}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    with pytest.raises(ValidationError, match="contains True or False"):
        schema.validate_file(files["config.yaml"])


def test_float_required_missing_field_rejected(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _required_float_schema_yaml(), "config.yaml": "{}"}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    with pytest.raises(ValidationError, match="Missing required field 'ratio'"):
        schema.validate_file(files["config.yaml"])


def test_float_optional_missing_field_uses_default(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _optional_float_schema_yaml("0.25"), "config.yaml": "{}"}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["ratio"] == 0.25
    assert data_with_default["ratio"] == 0.25


def test_float_optional_provided_value_overrides_default(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _optional_float_schema_yaml("0.25"), "config.yaml": "ratio: 0.5"}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["ratio"] == 0.5
    assert data_with_default["ratio"] == 0.5


def test_float_optional_without_default_rejected(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": """
                ratio:
                  type: float
                  description: Ratio value
                  required: false
            """,
            "config.yaml": "{}",
        }
    )

    with pytest.raises(ValidationError, match="invalid default value"):
        Schema.from_yaml(str(files["schema.yaml"]))


def test_float_with_min_max_rejects_below_min(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": """
                ratio:
                  type: float
                  description: Ratio value
                  required: true
                  min_value: 0.1
                  max_value: 1.0
            """,
            "config.yaml": "ratio: 0.01",
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    with pytest.raises(ValidationError, match="Value must be at least 0.1"):
        schema.validate_file(files["config.yaml"])


def test_float_with_min_max_accepts_edge_values(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": """
                ratio:
                  type: float
                  description: Ratio value
                  required: true
                  min_value: 0.1
                  max_value: 1.0
            """,
            "config.yaml": "ratio: 1.0",
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, _ = schema.validate_file(files["config.yaml"])
    assert built["ratio"] == 1.0
