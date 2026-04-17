import pytest

from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.schema import Schema


def _single_any_schema_yaml() -> str:
    return """
        payload:
          type: any
          description: Arbitrary payload
    """


def _optional_any_schema_yaml_without_default() -> str:
    return """
        payload:
          type: any
          description: Arbitrary payload
          required: false
    """


def _optional_any_schema_yaml_with_default() -> str:
    return """
        payload:
          type: any
          description: Arbitrary payload
          required: false
          default:
            source: schema-default
            retries: 3
    """


def test_any_file_config_with_null(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": _single_any_schema_yaml(),
            "config.yaml": """
                payload: null
            """,
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["payload"] is None
    assert data_with_default["payload"] is None


def test_any_file_config_with_bool(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": _single_any_schema_yaml(),
            "config.yaml": """
                payload: true
            """,
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["payload"] is True
    assert data_with_default["payload"] is True


def test_any_file_config_with_int(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": _single_any_schema_yaml(),
            "config.yaml": """
                payload: 123
            """,
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["payload"] == 123
    assert data_with_default["payload"] == 123


def test_any_file_config_with_float(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": _single_any_schema_yaml(),
            "config.yaml": """
                payload: 3.14
            """,
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["payload"] == 3.14
    assert data_with_default["payload"] == 3.14


def test_any_file_config_with_string(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": _single_any_schema_yaml(),
            "config.yaml": """
                payload: hello-world
            """,
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["payload"] == "hello-world"
    assert data_with_default["payload"] == "hello-world"


def test_any_file_config_with_list(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": _single_any_schema_yaml(),
            "config.yaml": """
                payload:
                  - 1
                  - two
                  - true
                  - null
            """,
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["payload"] == [1, "two", True, None]
    assert data_with_default["payload"] == [1, "two", True, None]


def test_any_file_config_with_object(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": _single_any_schema_yaml(),
            "config.yaml": """
                payload:
                  name: alpha
                  enabled: true
                  thresholds:
                    - 0.1
                    - 0.8
            """,
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["payload"] == {
        "name": "alpha",
        "enabled": True,
        "thresholds": [0.1, 0.8],
    }
    assert data_with_default["payload"] == built["payload"]


def test_any_optional_without_default_rejected(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": _optional_any_schema_yaml_without_default(),
            "config.yaml": """
                other: value
            """,
        }
    )

    with pytest.raises(ValidationError, match="optional AnyField must define an explicit default value"):
        Schema.from_yaml(str(files["schema.yaml"]))


def test_any_optional_missing_field_with_default_uses_default_value(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": _optional_any_schema_yaml_with_default(),
            "config.yaml": "{}",
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["payload"] == {"source": "schema-default", "retries": 3}
    assert data_with_default["payload"] == {"source": "schema-default", "retries": 3}


def test_any_optional_provided_value_overrides_default(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": _optional_any_schema_yaml_with_default(),
            "config.yaml": """
                payload:
                  source: config
                  retries: 9
            """,
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["payload"] == {"source": "config", "retries": 9}
    assert data_with_default["payload"] == {"source": "config", "retries": 9}


def test_any_optional_missing_payload_uses_default(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": _optional_any_schema_yaml_with_default(),
            "config.yaml": """
                note: payload intentionally omitted
            """,
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"], strict=False)

    assert built["payload"] == {"source": "schema-default", "retries": 3}
    assert data_with_default["payload"] == {"source": "schema-default", "retries": 3}
