import pytest

from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.schema import Schema


def _required_none_schema_yaml(type_literal: str = "None") -> str:
    return f"""
        value:
          type: {type_literal}
          description: Must be null/None
          required: true
    """


def _optional_none_schema_yaml_with_default(default_literal: str = "null") -> str:
    return f"""
        value:
          type: None
          description: Must be null/None
          required: false
          default: {default_literal}
    """


@pytest.mark.parametrize("type_literal", ["None", "none", "NONE"])
def test_none_required_schema_type_variations_are_supported(create_schema_examples, type_literal):
    files = create_schema_examples(
        {"schema.yaml": _required_none_schema_yaml(type_literal), "config.yaml": "value: null"}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["value"] is None
    assert data_with_default["value"] is None


def test_none_required_accepts_yaml_null(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _required_none_schema_yaml(), "config.yaml": "value: null"}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["value"] is None
    assert data_with_default["value"] is None


def test_none_required_accepts_none_string(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _required_none_schema_yaml(), "config.yaml": 'value: "None"'}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["value"] is None
    assert data_with_default["value"] == "None"


def test_none_required_accepts_null_string(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _required_none_schema_yaml(), "config.yaml": 'value: "null"'}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["value"] is None
    assert data_with_default["value"] == "null"


def test_none_required_missing_field_rejected(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _required_none_schema_yaml(), "config.yaml": "{}"}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    with pytest.raises(ValidationError, match="Missing required field 'value'"):
        schema.validate_file(files["config.yaml"])


@pytest.mark.parametrize("bad_value", ["true", "1", "abc", "[]", "{}"])
def test_none_required_rejects_invalid_values(create_schema_examples, bad_value):
    files = create_schema_examples(
        {"schema.yaml": _required_none_schema_yaml(), "config.yaml": f"value: {bad_value}"}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    with pytest.raises(ValidationError, match="must be null/None"):
        schema.validate_file(files["config.yaml"])


def test_none_optional_missing_field_uses_default_none(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _optional_none_schema_yaml_with_default("null"), "config.yaml": "{}"}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["value"] is None
    assert data_with_default["value"] is None


def test_none_optional_provided_value_keeps_none(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": _optional_none_schema_yaml_with_default("null"),
            "config.yaml": 'value: "None"',
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["value"] is None
    assert data_with_default["value"] == "None"


def test_none_optional_without_default_is_allowed_and_uses_none(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": """
                value:
                  type: None
                  description: Must be null/None
                  required: false
            """,
            "config.yaml": "{}",
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["value"] is None
    assert data_with_default["value"] is None


def test_none_optional_with_invalid_default_rejected(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": """
                value:
                  type: None
                  description: Must be null/None
                  required: false
                  default: true
            """,
            "config.yaml": "{}",
        }
    )

    with pytest.raises(ValidationError, match="invalid default value"):
        Schema.from_yaml(str(files["schema.yaml"]))
