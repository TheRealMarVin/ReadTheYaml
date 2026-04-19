import pytest

from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.schema import Schema


def _required_string_schema_yaml() -> str:
    return """
        title:
          type: str
          description: Display name
          required: true
    """


def _optional_string_schema_yaml(default_literal: str) -> str:
    return f"""
        title:
          type: str
          description: Display name
          required: false
          default: {default_literal}
    """


def test_string_required_accepts_string(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _required_string_schema_yaml(), "config.yaml": 'title: "alice"'}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["title"] == "alice"
    assert data_with_default["title"] == "alice"


def test_string_required_missing_field_rejected(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _required_string_schema_yaml(), "config.yaml": "{}"}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    with pytest.raises(ValidationError, match="Missing required field 'title'"):
        schema.validate_file(files["config.yaml"])


def test_string_required_rejects_non_string_by_default(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _required_string_schema_yaml(), "config.yaml": "title: 123"}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    with pytest.raises(ValidationError, match="Expected string"):
        schema.validate_file(files["config.yaml"])


def test_string_with_cast_to_string_accepts_int(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": """
                title:
                  type: str
                  description: Display name
                  required: true
                  cast_to_string: true
            """,
            "config.yaml": "title: 123",
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["title"] == "123"
    assert data_with_default["title"] == 123


def test_string_with_min_max_length_accepts_boundary_values(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": """
                title:
                  type: str
                  description: Display name
                  required: true
                  min_length: 2
                  max_length: 5
            """,
            "config.yaml": 'title: "abcde"',
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["title"] == "abcde"
    assert data_with_default["title"] == "abcde"


def test_string_with_min_length_rejects_short_value(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": """
                title:
                  type: str
                  description: Display name
                  required: true
                  min_length: 2
            """,
            "config.yaml": 'title: "a"',
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    with pytest.raises(ValidationError, match="at least 2 characters"):
        schema.validate_file(files["config.yaml"])


def test_string_with_max_length_rejects_long_value(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": """
                title:
                  type: str
                  description: Display name
                  required: true
                  max_length: 4
            """,
            "config.yaml": 'title: "alice"',
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    with pytest.raises(ValidationError, match="at most 4 characters"):
        schema.validate_file(files["config.yaml"])


def test_string_optional_missing_field_uses_default(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _optional_string_schema_yaml('"guest"'), "config.yaml": "{}"}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["title"] == "guest"
    assert data_with_default["title"] == "guest"


def test_string_optional_provided_value_overrides_default(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _optional_string_schema_yaml('"guest"'), "config.yaml": 'title: "root"'}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["title"] == "root"
    assert data_with_default["title"] == "root"


def test_string_optional_without_default_rejected(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": """
                title:
                  type: str
                  description: Display name
                  required: false
            """,
            "config.yaml": "{}",
        }
    )

    with pytest.raises(ValidationError, match="invalid default value"):
        Schema.from_yaml(str(files["schema.yaml"]))


def test_string_optional_with_invalid_default_rejected(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": """
                title:
                  type: str
                  description: Display name
                  required: false
                  default: 123
            """,
            "config.yaml": "{}",
        }
    )

    with pytest.raises(ValidationError, match="invalid default value"):
        Schema.from_yaml(str(files["schema.yaml"]))


def test_string_optional_default_violating_min_length_rejected(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": """
                title:
                  type: str
                  description: Display name
                  required: false
                  default: "a"
                  min_length: 2
            """,
            "config.yaml": "{}",
        }
    )

    with pytest.raises(ValidationError, match="invalid default value"):
        Schema.from_yaml(str(files["schema.yaml"]))
