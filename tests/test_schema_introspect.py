from readtheyaml.schema import Schema
from readtheyaml.ui.schema_helpers import flatten_field_paths
from readtheyaml.ui.schema_introspect import introspect_schema_dict


def test_introspect_primitive_fields_constraints_and_defaults():
    schema = Schema._from_dict(
            {
                "count": {"type": "int", "description": "Count", "min_value": 1, "max_value": 10},
                "service_name": {"type": "str", "description": "Name", "required": False, "default": "demo", "min_length": 2},
                "mode": {"type": "enum", "description": "Mode", "values": ["dev", "prod"]},
            }
        )

    ui = introspect_schema_dict(schema)
    fields = {item["key"]: item for item in ui["fields"]}

    assert ui["path"] == "<root>"
    assert fields["count"]["field_type"] == "int"
    assert fields["count"]["constraints"] == {"min": 1, "max": 10}

    assert fields["service_name"]["required"] is False
    assert fields["service_name"]["has_default"] is True
    assert fields["service_name"]["default"] == "demo"
    assert fields["service_name"]["constraints"] == {"min_length": 2}

    assert fields["mode"]["constraints"] == {"enum_values": ["dev", "prod"]}


def test_introspect_nested_sections_and_flatten_paths():
    schema = Schema._from_dict(
        {
            "service": {
                "description": "Service section",
                "host": {"type": "str", "description": "Host"},
                "port": {"type": "int", "description": "Port"},
            },
            "enabled": {"type": "bool", "description": "Enabled flag"},
        }
    )

    ui = introspect_schema_dict(schema)
    paths = flatten_field_paths(ui)

    assert paths == ["<root>.enabled", "<root>.service.host", "<root>.service.port"]


def test_introspect_preserves_schema_declaration_order():
    schema = Schema._from_dict(
        {
            "z_last": {"type": "str", "description": "z"},
            "a_first": {"type": "str", "description": "a"},
            "middle": {
                "description": "middle section",
                "z2": {"type": "int", "description": "z2"},
                "a2": {"type": "int", "description": "a2"},
            },
        }
    )
    ui = introspect_schema_dict(schema)
    assert [field["key"] for field in ui["fields"]] == ["z_last", "a_first"]
    assert [section["path"] for section in ui["subsections"]] == ["<root>.middle"]
    assert [field["key"] for field in ui["subsections"][0]["fields"]] == ["z2", "a2"]


def test_introspect_section_and_field_when_metadata_preserved():
    schema = Schema._from_dict(
        {
            "advanced_enabled": {
                "type": "bool",
                "description": "Toggle",
                "required": False,
                "default": False,
            },
            "advanced": {
                "required": False,
                "when": {"field": "advanced_enabled", "op": "eq", "value": True},
                "level": {
                    "type": "int",
                    "description": "Level",
                    "required": True,
                    "when": {"field": "advanced_enabled", "op": "eq", "value": True},
                },
            },
        }
    )

    ui = introspect_schema_dict(schema)
    subsection = ui["subsections"][0]
    field = subsection["fields"][0]

    assert subsection["path"] == "<root>.advanced"
    assert subsection["when"]["field"] == "advanced_enabled"
    assert subsection["when"]["op"] == "eq"
    assert subsection["when"]["value"] is True

    assert field["key"] == "level"
    assert field["when"]["field"] == "advanced_enabled"
    assert field["when"]["op"] == "eq"
    assert field["when"]["value"] is True
