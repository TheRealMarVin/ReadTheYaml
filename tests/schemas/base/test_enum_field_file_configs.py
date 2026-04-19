import pytest

from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.schema import Schema


def _required_enum_schema_yaml() -> str:
    return """
        mode:
          type: enum
          description: Running mode
          values: [auto, manual, off]
          required: true
    """


def _optional_enum_schema_yaml(default_literal: str) -> str:
    return f"""
        mode:
          type: enum
          description: Running mode
          values: [auto, manual, off]
          required: false
          default: {default_literal}
    """


def test_enum_required_accepts_auto(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _required_enum_schema_yaml(), "config.yaml": "mode: auto"}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["mode"] == "auto"
    assert data_with_default["mode"] == "auto"


def test_enum_required_accepts_manual(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _required_enum_schema_yaml(), "config.yaml": "mode: manual"}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["mode"] == "manual"
    assert data_with_default["mode"] == "manual"


def test_enum_required_missing_field_rejected(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _required_enum_schema_yaml(), "config.yaml": "{}"}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    with pytest.raises(ValidationError, match="Missing required field 'mode'"):
        schema.validate_file(files["config.yaml"])


def test_enum_required_rejects_value_not_in_choices(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _required_enum_schema_yaml(), "config.yaml": "mode: turbo"}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    with pytest.raises(ValidationError, match="Invalid value 'turbo'"):
        schema.validate_file(files["config.yaml"])


def test_enum_required_rejects_wrong_case_value(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _required_enum_schema_yaml(), "config.yaml": "mode: AUTO"}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    with pytest.raises(ValidationError, match="Invalid value 'AUTO'"):
        schema.validate_file(files["config.yaml"])


def test_enum_required_rejects_non_string_value(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _required_enum_schema_yaml(), "config.yaml": "mode: 1"}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    with pytest.raises(ValidationError, match="Invalid value '1'"):
        schema.validate_file(files["config.yaml"])


def test_enum_optional_missing_field_uses_default(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _optional_enum_schema_yaml("manual"), "config.yaml": "{}"}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["mode"] == "manual"
    assert data_with_default["mode"] == "manual"


def test_enum_optional_provided_value_overrides_default(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _optional_enum_schema_yaml("off"), "config.yaml": "mode: auto"}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["mode"] == "auto"
    assert data_with_default["mode"] == "auto"


def test_enum_optional_without_default_rejected(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": """
                mode:
                  type: enum
                  description: Running mode
                  values: [auto, manual, off]
                  required: false
            """,
            "config.yaml": "{}",
        }
    )

    with pytest.raises(ValidationError, match="invalid default value"):
        Schema.from_yaml(str(files["schema.yaml"]))


def test_enum_optional_with_invalid_default_rejected(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": """
                mode:
                  type: enum
                  description: Running mode
                  values: [auto, manual, off]
                  required: false
                  default: turbo
            """,
            "config.yaml": "{}",
        }
    )

    with pytest.raises(ValidationError, match="invalid default value"):
        Schema.from_yaml(str(files["schema.yaml"]))


def test_enum_schema_without_values_rejected(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": """
                mode:
                  type: enum
                  description: Running mode
            """,
            "config.yaml": "{}",
        }
    )

    with pytest.raises(ValidationError, match="EnumField requires a list of choices"):
        Schema.from_yaml(str(files["schema.yaml"]))


def test_enum_schema_with_empty_values_rejected(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": """
                mode:
                  type: enum
                  description: Running mode
                  values: []
            """,
            "config.yaml": "{}",
        }
    )

    with pytest.raises(ValidationError, match="EnumField requires a list of choices"):
        Schema.from_yaml(str(files["schema.yaml"]))
