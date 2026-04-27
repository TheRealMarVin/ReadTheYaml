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


def test_when_file_config_active_field_missing_required_raises(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": """
                compile_enabled:
                  type: bool
                  description: Compile toggle
                  required: false
                  default: false
                threads:
                  type: int
                  description: Thread count
                  required: true
                  when:
                    field: compile_enabled
                    op: eq
                    value: true
            """,
            "config.yaml": """
                compile_enabled: true
            """,
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    with pytest.raises(ValidationError, match="Missing required field 'threads'"):
        schema.validate_file(files["config.yaml"], strict=True)


def test_when_file_config_inactive_field_missing_required_is_skipped(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": """
                compile_enabled:
                  type: bool
                  description: Compile toggle
                  required: false
                  default: false
                threads:
                  type: int
                  description: Thread count
                  required: true
                  when:
                    field: compile_enabled
                    op: eq
                    value: true
            """,
            "config.yaml": """
                {}
            """,
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"], strict=True)

    assert built["compile_enabled"] is False
    assert "threads" not in built
    assert "threads" not in data_with_default


def test_when_file_config_all_condition_enforces_required_field(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": """
                compile_enabled:
                  type: bool
                  description: Compile toggle
                  required: false
                  default: false
                num_layers:
                  type: int
                  description: Layer count
                  required: false
                  default: 1
                compile_plan:
                  type: str
                  description: Deep compile plan
                  required: true
                  when:
                    all:
                      - field: compile_enabled
                        op: eq
                        value: true
                      - field: num_layers
                        op: gt
                        value: 5
            """,
            "config.yaml": """
                compile_enabled: true
                num_layers: 6
            """,
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    with pytest.raises(ValidationError, match="Missing required field 'compile_plan'"):
        schema.validate_file(files["config.yaml"], strict=True)


def test_when_file_config_any_condition_activates_required_field(create_schema_examples):
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
                deploy_target:
                  type: str
                  description: Deploy target
                  required: true
                  when:
                    any:
                      - field: mode
                        op: eq
                        value: prod
                      - field: force
                        op: eq
                        value: true
            """,
            "config.yaml": """
                force: true
            """,
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    with pytest.raises(ValidationError, match="Missing required field 'deploy_target'"):
        schema.validate_file(files["config.yaml"], strict=True)


def test_when_file_config_not_condition_disables_required_field(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": """
                dry_run:
                  type: bool
                  description: Dry run toggle
                  required: false
                  default: false
                publish_token:
                  type: str
                  description: Token required outside dry run
                  required: true
                  when:
                    not:
                      field: dry_run
                      op: eq
                      value: true
            """,
            "config.yaml": """
                dry_run: true
            """,
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"], strict=True)

    assert built["dry_run"] is True
    assert "publish_token" not in built
    assert "publish_token" not in data_with_default


def test_when_file_config_exists_on_nested_path_activates_required_field(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": """
                settings:
                  required: false
                  options:
                    required: false
                    flag:
                      type: bool
                      description: feature flag
                      required: false
                      default: true
                token:
                  type: str
                  description: required when nested flag exists
                  required: true
                  when:
                    field: settings.options.flag
                    op: exists
            """,
            "config.yaml": """
                settings:
                  options:
                    flag: false
            """,
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    with pytest.raises(ValidationError, match="Missing required field 'token'"):
        schema.validate_file(files["config.yaml"], strict=True)


def test_when_file_config_not_exists_on_nested_path_activates_required_field(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": """
                fallback_token:
                  type: str
                  description: required when nested value is missing
                  required: true
                  when:
                    field: settings.options.token
                    op: not_exists
            """,
            "config.yaml": """
                {}
            """,
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    with pytest.raises(ValidationError, match="Missing required field 'fallback_token'"):
        schema.validate_file(files["config.yaml"], strict=True)


def test_when_file_config_strict_mode_ignores_inactive_subsection_payload(create_schema_examples):
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
                  unknown: value
            """,
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"], strict=True)

    assert built["compile_enabled"] is False
    assert "compile" not in built
    assert "compile" not in data_with_default
