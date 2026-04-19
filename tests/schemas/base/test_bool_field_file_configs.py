import pytest

from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.schema import Schema


def _required_bool_schema_yaml() -> str:
    return """
        flag:
          type: bool
          description: Feature flag
          required: true
    """


def _optional_bool_schema_yaml(default_literal: str) -> str:
    return f"""
        flag:
          type: bool
          description: Feature flag
          required: false
          default: {default_literal}
    """


def test_bool_required_accepts_true(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _required_bool_schema_yaml(), "config.yaml": "flag: true"}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["flag"] is True
    assert data_with_default["flag"] is True


def test_bool_required_accepts_false(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _required_bool_schema_yaml(), "config.yaml": "flag: false"}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["flag"] is False
    assert data_with_default["flag"] is False


def test_bool_required_accepts_true_string_variation(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": _required_bool_schema_yaml(),
            "config.yaml": 'flag: "TrUe"',
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["flag"] is True
    assert data_with_default["flag"] == "TrUe"


def test_bool_required_accepts_false_string_variation(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": _required_bool_schema_yaml(),
            "config.yaml": 'flag: "fAlSe"',
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["flag"] is False
    assert data_with_default["flag"] == "fAlSe"


def test_bool_required_missing_field_rejected(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _required_bool_schema_yaml(), "config.yaml": "{}"}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    with pytest.raises(ValidationError, match="Missing required field 'flag'"):
        schema.validate_file(files["config.yaml"])


def test_bool_required_rejects_none_value(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _required_bool_schema_yaml(), "config.yaml": "flag: null"}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    with pytest.raises(ValidationError, match="Expected a boolean value, got NoneType"):
        schema.validate_file(files["config.yaml"])


def test_bool_required_rejects_null_string(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _required_bool_schema_yaml(), "config.yaml": 'flag: "null"'}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    with pytest.raises(ValidationError, match="contains None or null or empty"):
        schema.validate_file(files["config.yaml"])


def test_bool_required_rejects_empty_string(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _required_bool_schema_yaml(), "config.yaml": 'flag: ""'}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    with pytest.raises(ValidationError, match="contains None or null or empty"):
        schema.validate_file(files["config.yaml"])


def test_bool_required_rejects_invalid_string(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _required_bool_schema_yaml(), "config.yaml": 'flag: "yes"'}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    with pytest.raises(ValidationError, match="Expected a boolean value"):
        schema.validate_file(files["config.yaml"])


def test_bool_required_rejects_integer(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _required_bool_schema_yaml(), "config.yaml": "flag: 1"}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    with pytest.raises(ValidationError, match="Expected a boolean value, got int"):
        schema.validate_file(files["config.yaml"])


def test_bool_optional_missing_field_uses_default_true(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _optional_bool_schema_yaml("true"), "config.yaml": "{}"}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["flag"] is True
    assert data_with_default["flag"] is True


def test_bool_optional_provided_value_overrides_default(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _optional_bool_schema_yaml("false"), "config.yaml": "flag: true"}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["flag"] is True
    assert data_with_default["flag"] is True


def test_bool_optional_without_default_rejected(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": """
                flag:
                  type: bool
                  description: Feature flag
                  required: false
            """,
            "config.yaml": "{}",
        }
    )

    with pytest.raises(ValidationError, match="invalid default value"):
        Schema.from_yaml(str(files["schema.yaml"]))


def test_bool_optional_with_invalid_default_rejected(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": """
                flag:
                  type: bool
                  description: Feature flag
                  required: false
                  default: "yes"
            """,
            "config.yaml": "{}",
        }
    )

    with pytest.raises(ValidationError, match="invalid default value"):
        Schema.from_yaml(str(files["schema.yaml"]))
