import pytest

from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.schema import Schema


def test_ref_required_section_builds_and_applies_nested_defaults(create_schema_examples):
    files = create_schema_examples(
        {
            "shared/server.yaml": """
                host:
                  type: str
                  description: Host
                port:
                  type: int
                  description: Port
                  required: false
                  default: 8080
            """,
            "schema.yaml": """
                server:
                  $ref: shared/server.yaml
                  required: true
            """,
            "config.yaml": """
                server:
                  host: localhost
            """,
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["server"]["host"] == "localhost"
    assert built["server"]["port"] == 8080
    assert data_with_default["server"]["port"] == 8080


def test_ref_required_section_missing_is_rejected(create_schema_examples):
    files = create_schema_examples(
        {
            "shared/server.yaml": """
                host:
                  type: str
                  description: Host
            """,
            "schema.yaml": """
                server:
                  $ref: shared/server.yaml
                  required: true
            """,
            "config.yaml": "{}",
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    with pytest.raises(ValidationError, match="Missing required section 'server'"):
        schema.validate_file(files["config.yaml"])


def test_ref_optional_section_missing_defaults_to_none_even_if_nested_defaults_exist(create_schema_examples):
    files = create_schema_examples(
        {
            "shared/logging.yaml": """
                level:
                  type: str
                  description: Log level
                  required: false
                  default: info
                to_file:
                  type: bool
                  description: File logging
                  required: false
                  default: false
            """,
            "schema.yaml": """
                logging:
                  $ref: shared/logging.yaml
                  required: false
            """,
            "config.yaml": "{}",
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["logging"] is None
    assert data_with_default["logging"] is None


def test_ref_optional_section_present_is_validated_and_nested_defaults_apply(create_schema_examples):
    files = create_schema_examples(
        {
            "shared/logging.yaml": """
                level:
                  type: str
                  description: Log level
                  required: false
                  default: info
                to_file:
                  type: bool
                  description: File logging
                  required: false
                  default: false
            """,
            "schema.yaml": """
                logging:
                  $ref: shared/logging.yaml
                  required: false
            """,
            "config.yaml": """
                logging:
                  level: debug
            """,
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["logging"] == {"level": "debug", "to_file": False}
    assert data_with_default["logging"] == {"level": "debug", "to_file": False}


def test_ref_optional_section_present_with_invalid_type_is_rejected(create_schema_examples):
    files = create_schema_examples(
        {
            "shared/logging.yaml": """
                level:
                  type: str
                  description: Log level
                  required: false
                  default: info
                to_file:
                  type: bool
                  description: File logging
                  required: false
                  default: false
            """,
            "schema.yaml": """
                logging:
                  $ref: shared/logging.yaml
                  required: false
            """,
            "config.yaml": """
                logging: []
            """,
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    with pytest.raises(ValidationError, match="expects a mapping/dictionary"):
        schema.validate_file(files["config.yaml"])


def test_ref_optional_section_present_but_not_matching_schema_is_rejected(create_schema_examples):
    files = create_schema_examples(
        {
            "shared/logging.yaml": """
                level:
                  type: str
                  description: Log level
                  required: true
                to_file:
                  type: bool
                  description: File logging
                  required: false
                  default: false
            """,
            "schema.yaml": """
                logging:
                  $ref: shared/logging.yaml
                  required: false
            """,
            "config.yaml": """
                logging: {}
            """,
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    with pytest.raises(ValidationError, match="Missing required field 'level'"):
        schema.validate_file(files["config.yaml"])


def test_ref_optional_section_present_as_null_is_rejected(create_schema_examples):
    files = create_schema_examples(
        {
            "shared/logging.yaml": """
                level:
                  type: str
                  description: Log level
                  required: false
                  default: info
            """,
            "schema.yaml": """
                logging:
                  $ref: shared/logging.yaml
                  required: false
            """,
            "config.yaml": """
                logging: null
            """,
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    with pytest.raises(ValidationError, match="expects a mapping/dictionary"):
        schema.validate_file(files["config.yaml"])


def test_ref_optional_section_explicit_default_is_used_when_missing(create_schema_examples):
    files = create_schema_examples(
        {
            "shared/logging.yaml": """
                level:
                  type: str
                  description: Log level
                  required: false
                  default: info
            """,
            "schema.yaml": """
                logging:
                  $ref: shared/logging.yaml
                  required: false
                  default:
                    level: warn
            """,
            "config.yaml": "{}",
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["logging"] == {"level": "warn"}
    assert data_with_default["logging"] == {"level": "warn"}


def test_ref_missing_file_is_rejected(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": """
                logging:
                  $ref: shared/missing.yaml
                  required: true
            """,
            "config.yaml": "{}",
        }
    )

    with pytest.raises(FileNotFoundError, match="Referenced schema file not found"):
        Schema.from_yaml(str(files["schema.yaml"]))


def test_ref_target_with_non_mapping_content_is_rejected(create_schema_examples):
    files = create_schema_examples(
        {
            "shared/logging.yaml": """
                - not
                - a
                - mapping
            """,
            "schema.yaml": """
                logging:
                  $ref: shared/logging.yaml
                  required: true
            """,
            "config.yaml": "{}",
        }
    )

    with pytest.raises(ValidationError, match="Schema definition must be a mapping/dictionary"):
        Schema.from_yaml(str(files["schema.yaml"]))


def test_ref_nested_relative_refs_are_resolved_from_ref_file_directory(create_schema_examples):
    files = create_schema_examples(
        {
            "shared/sections/logging.yaml": """
                details:
                  $ref: ./details.yaml
                  required: true
            """,
            "shared/sections/details.yaml": """
                level:
                  type: str
                  description: Log level
                  required: true
            """,
            "schema.yaml": """
                logging:
                  $ref: shared/sections/logging.yaml
                  required: true
            """,
            "config.yaml": """
                logging:
                  details:
                    level: debug
            """,
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, _ = schema.validate_file(files["config.yaml"])

    assert built["logging"]["details"]["level"] == "debug"


def test_ref_present_section_rejects_extra_keys_in_strict_mode(create_schema_examples):
    files = create_schema_examples(
        {
            "shared/logging.yaml": """
                level:
                  type: str
                  description: Log level
                  required: true
            """,
            "schema.yaml": """
                logging:
                  $ref: shared/logging.yaml
                  required: true
            """,
            "config.yaml": """
                logging:
                  level: debug
                  extra: nope
            """,
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    with pytest.raises(ValidationError, match="Unexpected key\\(s\\) in section"):
        schema.validate_file(files["config.yaml"], strict=True)
