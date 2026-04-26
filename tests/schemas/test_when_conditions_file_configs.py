import pytest

from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.schema import Schema


def test_when_file_config_inactive_subsection_is_skipped(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": """
                compile_enabled:
                  type: bool
                  description: Compile toggle
                  required: false
                  default: false
                compile:
                  required: false
                  when:
                    field: compile_enabled
                    op: eq
                    value: true
                  command:
                    type: str
                    description: Compile command
                    required: true
            """,
            "config.yaml": """
                compile:
                  command: 123
                  extra: ignored
            """,
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"], strict=True)

    assert built["compile_enabled"] is False
    assert "compile" not in built
    assert "compile" not in data_with_default


def test_when_file_config_active_subsection_is_validated(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": """
                compile_enabled:
                  type: bool
                  description: Compile toggle
                  required: false
                  default: false
                compile:
                  required: false
                  when:
                    field: compile_enabled
                    op: eq
                    value: true
                  command:
                    type: str
                    description: Compile command
                    required: true
            """,
            "config.yaml": """
                compile_enabled: true
                compile: {}
            """,
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    with pytest.raises(ValidationError, match="Missing required field 'command'"):
        schema.validate_file(files["config.yaml"], strict=True)


def test_when_file_config_combinators_work(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": """
                mode:
                  type: str
                  description: Build mode
                  required: false
                  default: dev
                force:
                  type: bool
                  description: Force build
                  required: false
                  default: false
                deploy:
                  type: str
                  description: Deploy target
                  required: true
                  when:
                    all:
                      - any:
                          - field: mode
                            op: in
                            value: [prod, stage]
                          - field: force
                            op: eq
                            value: true
                      - not:
                          field: mode
                          op: eq
                          value: dry-run
            """,
            "config.yaml": """
                mode: dev
            """,
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, _ = schema.validate_file(files["config.yaml"], strict=True)

    assert "deploy" not in built
