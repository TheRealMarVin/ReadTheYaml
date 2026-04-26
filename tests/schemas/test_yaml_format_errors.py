import pytest

from readtheyaml.exceptions.format_error import FormatError
from readtheyaml.schema import Schema


def test_from_yaml_with_malformed_schema_reports_file_in_error(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": """
                app:
                  type: str
                  default: [1, 2
            """,
        }
    )

    with pytest.raises(FormatError) as exc:
        Schema.from_yaml(str(files["schema.yaml"]))

    message = str(exc.value)
    assert "Invalid YAML format in" in message
    assert "schema.yaml" in message


def test_validate_file_with_malformed_config_reports_file_in_error(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": """
                app:
                  type: str
                  description: app name
            """,
            "config.yaml": """
                app: [foo
            """,
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))

    with pytest.raises(FormatError) as exc:
        schema.validate_file(files["config.yaml"])

    message = str(exc.value)
    assert "Invalid YAML format in" in message
    assert "config.yaml" in message
