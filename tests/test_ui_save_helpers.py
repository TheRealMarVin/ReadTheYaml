from datetime import timedelta

import pytest

from readtheyaml.ui.save_helpers import SAVE_MODE_EXPORT, SAVE_MODE_FULL, can_save, get_save_payload, serialize_yaml


def test_serialize_yaml_ends_with_newline():
    text = serialize_yaml({"name": "demo"})
    assert text.endswith("\n")
    assert "name: demo" in text


def test_serialize_yaml_supports_timedelta():
    text = serialize_yaml({"delay": timedelta(seconds=30)})
    assert "delay:" in text
    assert "seconds: 30" in text


def test_serialize_yaml_keeps_tuple_as_literal_string():
    text = serialize_yaml({"pair": (1, "alpha")})
    assert "pair: (1, 'alpha')" in text


def test_serialize_yaml_keeps_list_as_yaml_list():
    text = serialize_yaml({"items": [1, 2, 3]})
    assert "items: [1, 2, 3]" in text


def test_can_save_blocks_invalid():
    allowed, reason = can_save(False)
    assert allowed is False
    assert "invalid" in reason.lower()


def test_can_save_allows_valid():
    allowed, reason = can_save(True)
    assert allowed is True
    assert reason is None


def test_get_save_payload_export_mode():
    payload = get_save_payload(SAVE_MODE_EXPORT, {"a": 1}, {"a": 2})
    assert payload == {"a": 1}


def test_get_save_payload_full_mode():
    payload = get_save_payload(SAVE_MODE_FULL, {"a": 1}, {"a": 2})
    assert payload == {"a": 2}


def test_get_save_payload_full_requires_defaults_data():
    with pytest.raises(ValueError):
        get_save_payload(SAVE_MODE_FULL, {"a": 1}, None)


def test_get_save_payload_export_omits_schema_defaults():
    schema_model = {
        "path": "<root>",
        "fields": [{"key": "enabled", "has_default": True, "default": True}],
        "subsections": [
            {
                "path": "<root>.service",
                "fields": [{"key": "port", "has_default": True, "default": 8080}],
                "subsections": [],
            }
        ],
    }
    payload = get_save_payload(
        SAVE_MODE_EXPORT,
        {"enabled": True, "service": {"port": 8080, "name": "api"}},
        {"enabled": True, "service": {"port": 8080, "name": "api"}},
        schema_model=schema_model,
    )
    assert payload == {"service": {"name": "api"}}


def test_get_save_payload_excludes_inactive_when_field_and_section():
    schema_model = {
        "path": "<root>",
        "fields": [
            {"key": "enabled", "has_default": False},
            {"key": "token", "has_default": False, "when": {"kind": "atomic", "field": "enabled", "op": "eq", "value": True}},
        ],
        "subsections": [
            {
                "path": "<root>.deploy",
                "when": {"kind": "atomic", "field": "enabled", "op": "eq", "value": True},
                "fields": [{"key": "target", "has_default": False}],
                "subsections": [],
            }
        ],
    }
    payload = get_save_payload(
        SAVE_MODE_FULL,
        {"enabled": False, "token": "secret", "deploy": {"target": "prod"}},
        {"enabled": False, "token": "secret", "deploy": {"target": "prod"}},
        schema_model=schema_model,
    )
    assert payload == {"enabled": False}
