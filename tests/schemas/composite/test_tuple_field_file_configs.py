import pytest

from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.schema import Schema


def _required_tuple_schema_yaml() -> str:
    return """
        pair:
          type: tuple[int, str]
          description: Integer/string pair
          required: true
    """


def _optional_tuple_schema_yaml(default_literal: str) -> str:
    return f"""
        pair:
          type: tuple[int, str]
          description: Integer/string pair
          required: false
          default: {default_literal}
    """


def test_tuple_required_accepts_tuple_string(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": _required_tuple_schema_yaml(),
            "config.yaml": 'pair: "(1, \'alpha\')"',
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["pair"] == (1, "alpha")
    assert data_with_default["pair"] == "(1, 'alpha')"


def test_tuple_required_missing_field_rejected(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _required_tuple_schema_yaml(), "config.yaml": "{}"}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    with pytest.raises(ValidationError, match="Missing required field 'pair'"):
        schema.validate_file(files["config.yaml"])


def test_tuple_required_rejects_wrong_arity(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": _required_tuple_schema_yaml(),
            "config.yaml": 'pair: "(1, \'alpha\', 3)"',
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    with pytest.raises(ValidationError, match="exactly 2 elements"):
        schema.validate_file(files["config.yaml"])


def test_tuple_required_rejects_invalid_element_type(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": _required_tuple_schema_yaml(),
            "config.yaml": 'pair: "(1, 2)"',
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    with pytest.raises(ValidationError, match="Tuple element 1 invalid"):
        schema.validate_file(files["config.yaml"])


def test_tuple_required_rejects_yaml_list_input(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": _required_tuple_schema_yaml(),
            "config.yaml": """
                pair:
                  - 1
                  - alpha
            """,
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    with pytest.raises(ValidationError, match="Not a valid tuple"):
        schema.validate_file(files["config.yaml"])


def test_tuple_optional_missing_field_uses_default(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _optional_tuple_schema_yaml('"(7, \'seed\')"'), "config.yaml": "{}"}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["pair"] == (7, "seed")
    assert data_with_default["pair"] == (7, "seed")


def test_tuple_optional_provided_value_overrides_default(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": _optional_tuple_schema_yaml('"(7, \'seed\')"'),
            "config.yaml": 'pair: "(3, \'live\')"',
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["pair"] == (3, "live")
    assert data_with_default["pair"] == "(3, 'live')"


def test_tuple_optional_without_default_rejected(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": """
                pair:
                  type: tuple[int, str]
                  description: Integer/string pair
                  required: false
            """,
            "config.yaml": "{}",
        }
    )

    with pytest.raises(ValidationError, match="invalid default value"):
        Schema.from_yaml(str(files["schema.yaml"]))


def test_tuple_with_bool_and_float_elements(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": """
                pair:
                  type: tuple[bool, float]
                  description: Bool/float pair
                  required: true
            """,
            "config.yaml": 'pair: "(\'TrUe\', 1e-2)"',
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["pair"] == ("TrUe", 0.01)
    assert data_with_default["pair"] == "('TrUe', 1e-2)"
