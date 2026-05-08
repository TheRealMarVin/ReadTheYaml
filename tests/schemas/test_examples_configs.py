from pathlib import Path

import pytest
import yaml

from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.schema import Schema


def _examples_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "examples"


@pytest.mark.parametrize(
    ("schema_file", "config_file"),
    [
        ("schema.yaml", "config.yaml"),
        ("schema_composed.yaml", "config_composed.yaml"),
        ("schema_all_types.yaml", "config_all_types.yaml"),
    ],
)
def test_all_examples_configs_validate(schema_file: str, config_file: str):
    examples_dir = _examples_dir()
    schema = Schema.from_yaml(str(examples_dir / schema_file))
    built, data_with_default = schema.validate_file(examples_dir / config_file, strict=True)

    assert isinstance(built, dict)
    assert isinstance(data_with_default, dict)


def test_composed_example_config_is_valid_and_defaults_are_applied():
    examples_dir = _examples_dir()
    schema = Schema.from_yaml(str(examples_dir / "schema_composed.yaml"))

    built, data_with_default = schema.validate_file(examples_dir / "config_composed.yaml", strict=True)

    assert built["service_name"] == "api-gateway"
    assert built["environment"] == "prod"
    assert built["network"]["port"] == 8080
    assert built["observability"]["trace_sampling_rate"] == 0.1
    assert data_with_default["runtime"]["request_timeout_seconds"] == 5.0


def test_composed_example_schema_requires_deployment_when_environment_is_prod(tmp_path: Path):
    examples_dir = _examples_dir()
    schema = Schema.from_yaml(str(examples_dir / "schema_composed.yaml"))

    config = yaml.safe_load((examples_dir / "config_composed.yaml").read_text(encoding="utf-8"))
    config.pop("deployment", None)

    invalid_path = tmp_path / "config_missing_deployment.yaml"
    invalid_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")

    with pytest.raises(ValidationError, match="Missing required section 'deployment'"):
        schema.validate_file(invalid_path, strict=True)
