import pytest

from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.schema import Schema


def _required_int_list_schema_yaml() -> str:
    return """
        entries:
          type: list[int]
          description: Integer entries
          required: true
    """


def _optional_int_list_schema_yaml(default_yaml: str) -> str:
    return f"""
        entries:
          type: list[int]
          description: Integer entries
          required: false
          default:
{default_yaml}
    """


def test_list_required_accepts_valid_int_list(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": _required_int_list_schema_yaml(),
            "config.yaml": """
                entries:
                  - 1
                  - 2
                  - 3
            """,
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["entries"] == [1, 2, 3]
    assert data_with_default["entries"] == [1, 2, 3]


def test_list_required_accepts_numeric_strings_and_keeps_raw_config(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": _required_int_list_schema_yaml(),
            "config.yaml": """
                entries:
                  - "1"
                  - "2"
            """,
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["entries"] == [1, 2]
    assert data_with_default["entries"] == ["1", "2"]


def test_list_required_missing_field_rejected(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _required_int_list_schema_yaml(), "config.yaml": "{}"}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    with pytest.raises(ValidationError, match="Missing required field 'entries'"):
        schema.validate_file(files["config.yaml"])


def test_list_required_rejects_non_list_value(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _required_int_list_schema_yaml(), "config.yaml": "entries: 1"}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    with pytest.raises(ValidationError, match="Expected a list"):
        schema.validate_file(files["config.yaml"])


def test_list_required_rejects_invalid_item_type(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": _required_int_list_schema_yaml(),
            "config.yaml": """
                entries:
                  - 1
                  - bad
            """,
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    with pytest.raises(ValidationError, match="Invalid item at index 1"):
        schema.validate_file(files["config.yaml"])


def test_list_optional_missing_field_uses_default(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": _optional_int_list_schema_yaml("            - 7\n            - 8"),
            "config.yaml": "{}",
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["entries"] == [7, 8]
    assert data_with_default["entries"] == [7, 8]


def test_list_optional_provided_value_overrides_default(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": _optional_int_list_schema_yaml("            - 7\n            - 8"),
            "config.yaml": """
                entries:
                  - 3
            """,
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["entries"] == [3]
    assert data_with_default["entries"] == [3]


def test_list_optional_without_default_rejected(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": """
                entries:
                  type: list[int]
                  description: Integer entries
                  required: false
            """,
            "config.yaml": "{}",
        }
    )

    with pytest.raises(ValidationError, match="invalid default value"):
        Schema.from_yaml(str(files["schema.yaml"]))


def test_list_with_length_range_accepts_boundary(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": """
                entries:
                  type: list[int]
                  description: Integer entries
                  required: true
                  length_range: [2, 3]
            """,
            "config.yaml": """
                entries:
                  - 10
                  - 20
                  - 30
            """,
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, _ = schema.validate_file(files["config.yaml"])
    assert built["entries"] == [10, 20, 30]


def test_list_with_length_range_rejects_too_short(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": """
                entries:
                  type: list[int]
                  description: Integer entries
                  required: true
                  length_range: [2, 3]
            """,
            "config.yaml": """
                entries:
                  - 10
            """,
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    with pytest.raises(ValidationError, match="at least 2 items"):
        schema.validate_file(files["config.yaml"])


def test_list_with_length_range_rejects_too_long(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": """
                entries:
                  type: list[int]
                  description: Integer entries
                  required: true
                  length_range: [2, 3]
            """,
            "config.yaml": """
                entries:
                  - 10
                  - 20
                  - 30
                  - 40
            """,
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    with pytest.raises(ValidationError, match="at most 3 items"):
        schema.validate_file(files["config.yaml"])


def test_list_of_bool_accepts_boolean_string_variations(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": """
                entries:
                  type: list[bool]
                  description: Boolean entries
                  required: true
            """,
            "config.yaml": """
                entries:
                  - "TrUe"
                  - "fAlSe"
                  - true
                  - false
            """,
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["entries"] == [True, False, True, False]
    assert data_with_default["entries"] == ["TrUe", "fAlSe", True, False]
