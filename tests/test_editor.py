from pathlib import Path

import pytest

from readtheyaml.editor import load_schema_and_config, parse_args
from readtheyaml.exceptions.validation_error import ValidationError


def _write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def test_parse_args_defaults_strict_true():
    args = parse_args(["--schema", "schema.yaml"])
    assert args.schema == "schema.yaml"
    assert args.config is None
    assert args.strict is True


@pytest.mark.parametrize(("raw", "expected"), [("true", True), ("false", False)])
def test_parse_args_strict_boolean_values(raw: str, expected: bool):
    args = parse_args(["--schema", "schema.yaml", "--strict", raw])
    assert args.strict is expected


def test_load_schema_and_config_without_config_uses_empty_dict(tmp_path: Path):
    schema_path = tmp_path / "schema.yaml"
    _write_text(
        schema_path,
        "name: sample\n"
        "optional_text:\n"
        "  type: str\n"
        "  description: Optional text\n"
        "  required: false\n"
        "  default: hello\n",
    )

    _, config = load_schema_and_config(str(schema_path), None, strict=True)
    assert config == {}


def test_load_schema_and_config_loads_config_and_validates(tmp_path: Path):
    schema_path = tmp_path / "schema.yaml"
    config_path = tmp_path / "config.yaml"
    _write_text(
        schema_path,
        "name: sample\n"
        "count:\n"
        "  type: int\n"
        "  description: Count\n",
    )
    _write_text(config_path, "count: 3\n")

    _, config = load_schema_and_config(str(schema_path), str(config_path), strict=True)
    assert config == {"count": 3}


def test_load_schema_and_config_invalid_config_raises_validation_error(tmp_path: Path):
    schema_path = tmp_path / "schema.yaml"
    config_path = tmp_path / "config.yaml"
    _write_text(
        schema_path,
        "name: sample\n"
        "count:\n"
        "  type: int\n"
        "  description: Count\n",
    )
    _write_text(config_path, "count: nope\n")

    with pytest.raises(ValidationError, match="Must be of type int"):
        load_schema_and_config(str(schema_path), str(config_path), strict=True)


def test_load_schema_and_config_allows_partial_config_missing_required_fields(tmp_path: Path):
    schema_path = tmp_path / "schema.yaml"
    config_path = tmp_path / "config.yaml"
    _write_text(
        schema_path,
        "name: sample\n"
        "service_name:\n"
        "  type: str\n"
        "  description: Service name\n",
    )
    _write_text(config_path, "{}\n")

    _, config = load_schema_and_config(str(schema_path), str(config_path), strict=True)
    assert config == {}
