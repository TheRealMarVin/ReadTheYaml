from readtheyaml.ui.form_renderer import (
    evaluate_visibility_map,
    get_value_at_path,
    materialize_section_path,
    project_known_config,
    resolve_display_value,
    set_value_at_path,
)


def test_get_and_set_value_at_path():
    data = {}
    set_value_at_path(data, "service.host", "localhost")
    set_value_at_path(data, "service.port", 8080)

    assert data == {"service": {"host": "localhost", "port": 8080}}
    assert get_value_at_path(data, "service.host") == "localhost"
    assert get_value_at_path(data, "service.missing", default="x") == "x"


def test_materialize_section_path_creates_nested_dicts():
    data = {}
    node = materialize_section_path(data, "service.logging")

    assert isinstance(node, dict)
    assert data == {"service": {"logging": {}}}


def test_project_known_config_drops_unknown_keys_for_strict_mode_behavior():
    model = {
        "path": "<root>",
        "fields": [{"key": "service_name"}],
        "subsections": [
            {
                "path": "<root>.service",
                "fields": [{"key": "host"}],
                "subsections": [],
            }
        ],
    }
    config = {
        "service_name": "app",
        "service": {"host": "127.0.0.1", "extra": "drop-me"},
        "unknown": 123,
    }

    projected = project_known_config(config, model)
    assert projected == {"service_name": "app", "service": {"host": "127.0.0.1"}}


def test_visibility_map_field_when_transitions_true_false():
    model = {
        "path": "<root>",
        "fields": [
            {"key": "enabled"},
            {"key": "token", "when": {"kind": "atomic", "field": "enabled", "op": "eq", "value": True}},
        ],
        "subsections": [],
    }
    off = evaluate_visibility_map(model, {"enabled": False})
    on = evaluate_visibility_map(model, {"enabled": True})

    assert off["token"] is False
    assert on["token"] is True


def test_visibility_map_section_when_transitions_true_false():
    model = {
        "path": "<root>",
        "fields": [{"key": "mode"}],
        "subsections": [
            {
                "path": "<root>.deploy",
                "when": {"kind": "atomic", "field": "mode", "op": "eq", "value": "prod"},
                "fields": [{"key": "target"}],
                "subsections": [],
            }
        ],
    }
    dev = evaluate_visibility_map(model, {"mode": "dev"})
    prod = evaluate_visibility_map(model, {"mode": "prod"})

    assert dev["deploy"] is False
    assert dev["deploy.target"] is False
    assert prod["deploy"] is True
    assert prod["deploy.target"] is True


def test_visibility_map_nested_dependencies_respect_parent_activity():
    model = {
        "path": "<root>",
        "fields": [{"key": "enabled"}],
        "subsections": [
            {
                "path": "<root>.advanced",
                "when": {"kind": "atomic", "field": "enabled", "op": "eq", "value": True},
                "fields": [{"key": "mode"}],
                "subsections": [
                    {
                        "path": "<root>.advanced.nested",
                        "when": {"kind": "atomic", "field": "advanced.mode", "op": "eq", "value": "x"},
                        "fields": [{"key": "value"}],
                        "subsections": [],
                    }
                ],
            }
        ],
    }
    inactive_parent = evaluate_visibility_map(model, {"enabled": False, "advanced": {"mode": "x"}})
    active_parent = evaluate_visibility_map(model, {"enabled": True, "advanced": {"mode": "x"}})

    assert inactive_parent["advanced"] is False
    assert inactive_parent["advanced.nested"] is False
    assert inactive_parent["advanced.nested.value"] is False
    assert active_parent["advanced"] is True
    assert active_parent["advanced.nested"] is True
    assert active_parent["advanced.nested.value"] is True


def test_resolve_display_value_uses_schema_default_only_when_missing():
    field_model = {"key": "port", "has_default": True, "default": 8080}

    assert resolve_display_value(field_model, {}, "service.port") == 8080
    assert resolve_display_value(field_model, {"service": {"port": 9090}}, "service.port") == 9090

