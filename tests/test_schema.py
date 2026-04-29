from readtheyaml.exceptions.format_error import FormatError
from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.fields.field_helpers import get_reserved_keywords_by_loaded_fields
from readtheyaml.schema import Schema

import pytest

# -------------------
# Tests Other
# -------------------
@pytest.mark.parametrize("reserved_keyword", sorted(set().union(*get_reserved_keywords_by_loaded_fields().values())))
def test_reserved_keyword_as_field_name(reserved_keyword):
    """Test that reserved names are handled correctly and raise FormatError."""
    bad_schema = {
        reserved_keyword: {
            "type": "int",
            "default": 3,
            "description": "some field"
        }
    }

    with pytest.raises(FormatError, match="reserved"):
        Schema._from_dict(bad_schema)


def test_when_is_not_treated_as_reserved_field_name():
    reserved_keywords = set().union(*get_reserved_keywords_by_loaded_fields().values())
    assert "when" not in reserved_keywords


@pytest.mark.parametrize(
    "field_definition",
    [
        {"type": "int", "description": "int field"},
        {"type": "str", "description": "string field"},
        {"type": "bool", "description": "bool field"},
        {"type": "enum", "values": ["a", "b"], "description": "enum field"},
        {"type": "list(int)", "description": "list field"},
        {"type": "tuple(int, str)", "description": "tuple field"},
        {"type": "int|str", "description": "union field"},
    ],
)
def test_when_is_allowed_as_field_name_for_supported_field_shapes(field_definition):
    schema_dict = {"when": field_definition}

    schema = Schema._from_dict(schema_dict)

    assert "when" in schema.fields

@pytest.mark.parametrize(
    "field_definition",
    [
        {"type": "int", "default": 3, "description": "int field"},
        {"type": "str", "default": "abc", "description": "string field"},
        {"type": "bool", "default": True, "description": "bool field"},
        {"type": "enum", "values": ["a", "b"], "default": "a", "description": "enum field"},
        {"type": "list(int)", "default": [1, 2], "description": "list field"},
        {"type": "tuple(int, str)", "default": "(1, 'a')", "description": "tuple field"},
        {"type": "int|str", "default": 1, "description": "union field"},
    ],
)
@pytest.mark.parametrize("reserved_keyword", sorted(set().union(*get_reserved_keywords_by_loaded_fields().values())))
def test_reserved_keyword_rejected_for_various_field_types(reserved_keyword, field_definition):
    """Reserved field names should be rejected regardless of declared field type."""
    bad_schema = {
        reserved_keyword: field_definition
    }

    with pytest.raises(FormatError, match="reserved"):
        Schema._from_dict(bad_schema)

def test_schema_missing_required_field_raises():
    """Missing a required field should raise ValidationError."""
    schema_dict = {
        "full_name": {
            "type": "str",
            "description": "Name is required"
        }
    }
    schema = Schema._from_dict(schema_dict)

    data = {}
    with pytest.raises(ValidationError, match="Missing required field 'full_name'"):
        schema.build_and_validate(data)


def test_schema_adds_default_value_when_missing():
    """Default values should be inserted into output if data omits them."""
    schema_dict = {
        "level": {
            "type": "int",
            "default": 1,
            "required": False,
            "description": "Optional level"
        }
    }
    schema = Schema._from_dict(schema_dict)
    built, data_with_default = schema.build_and_validate({})
    assert built["level"] == 1
    assert data_with_default["level"] == 1

def test_schema_rejects_unknown_field_in_strict_mode():
    """Unknown keys in input raise error when strict=True."""
    schema_dict = {
        "id": {
            "type": "int",
            "description": "User ID"
        }
    }
    schema = Schema._from_dict(schema_dict)
    with pytest.raises(ValidationError, match="Unexpected key"):
        schema.build_and_validate({"id": 1, "extra": "oops"}, strict=True)

def test_schema_accepts_unknown_field_in_non_strict_mode():
    """Unknown keys are preserved in output if strict=False."""
    schema_dict = {
        "id": {
            "type": "int",
            "description": "User ID"
        }
    }
    schema = Schema._from_dict(schema_dict)
    data = {"id": 1, "extra": "ok"}
    built, _ = schema.build_and_validate(data, strict=False)
    assert built["id"] == 1
    assert built["extra"] == "ok"

def test_schema_strict_mode_reports_exact_unexpected_keys_message():
    """Strict mode should report sorted unexpected keys and root section name."""
    schema_dict = {
        "id": {
            "type": "int",
            "description": "User ID"
        }
    }
    schema = Schema._from_dict(schema_dict)

    with pytest.raises(ValidationError) as exc:
        schema.build_and_validate({"id": 1, "z": 9, "a": 2}, strict=True)

    assert str(exc.value) == "Unexpected key(s) in section '<root>': a, z"

@pytest.mark.parametrize("strict_mode", [True, False])
def test_schema_type_mismatch_reports_same_error_in_strict_and_non_strict(strict_mode):
    """Type mismatch should raise the same field-level message in both modes."""
    schema_dict = {
        "count": {
            "type": "int",
            "description": "Count value"
        }
    }
    schema = Schema._from_dict(schema_dict)

    with pytest.raises(ValidationError) as exc:
        schema.build_and_validate({"count": "not-an-int"}, strict=strict_mode)

    assert str(exc.value) == "Field 'count': Must be of type int"

def test_schema_with_nested_subsection():
    """Subsections should be recursively validated."""
    schema_dict = {
        "meta": {
            "description": "metadata section",
            "required": True,
            "version": {
                "type": "int",
                "description": "Version number"
            },
            "author": {
                "type": "str",
                "description": "Author name"
            }
        }
    }
    schema = Schema._from_dict(schema_dict)
    data = {"meta": {"version": 1, "author": "Vincent"}}
    built, _ = schema.build_and_validate(data)
    assert built["meta"]["author"] == "Vincent"

def test_schema_nested_missing_required_field():
    """Missing required field inside nested section should raise error."""
    schema_dict = {
        "settings": {
            "description": "config section",
            "required": True,
            "theme": {
                "type": "str",
                "description": "UI theme"
            },
            "timeout": {
                "type": "int",
                "description": "Request timeout"
            }
        }
    }
    schema = Schema._from_dict(schema_dict)
    data = {"settings": {"theme": "dark"}}
    with pytest.raises(ValidationError, match="Missing required field 'timeout'"):
        schema.build_and_validate(data)

def test_schema_optional_subsection_not_provided():
    """Missing optional subsection without explicit default should be omitted."""
    schema_dict = {
        "optional_section": {
            "description": "optional config",
            "required": False,
            "enabled": {
                "type": "bool",
                "description": "Whether enabled",
                "required": False,
                "default": False
            }
        }
    }
    schema = Schema._from_dict(schema_dict)
    built, data_with_default = schema.build_and_validate({})

    assert "optional_section" not in built
    assert "optional_section" not in data_with_default

def test_schema_optional_subsection_with_none_default_not_expanded():
    """Optional subsection with default=None should stay None and not inject child defaults."""
    schema_dict = {
        "optional_section": {
            "description": "optional config",
            "required": False,
            "default": None,
            "enabled": {
                "type": "bool",
                "description": "Whether enabled",
                "required": False,
                "default": False
            }
        }
    }
    schema = Schema._from_dict(schema_dict)
    built, data_with_default = schema.build_and_validate({})

    assert "optional_section" in built
    assert built["optional_section"] is None
    assert data_with_default["optional_section"] is None


def test_schema_when_inactive_field_is_skipped_even_if_present():
    schema_dict = {
        "compile_enabled": {
            "type": "bool",
            "description": "compile toggle",
            "required": False,
            "default": False,
        },
        "threads": {
            "type": "int",
            "description": "thread count",
            "required": True,
            "when": {"field": "compile_enabled", "op": "eq", "value": True},
        },
    }
    schema = Schema._from_dict(schema_dict)

    built, data_with_default = schema.build_and_validate({"threads": "not-an-int"}, strict=True)

    assert built["compile_enabled"] is False
    assert "threads" not in built
    assert "threads" not in data_with_default


def test_schema_when_active_field_is_validated():
    schema_dict = {
        "compile_enabled": {
            "type": "bool",
            "description": "compile toggle",
            "required": False,
            "default": False,
        },
        "threads": {
            "type": "int",
            "description": "thread count",
            "required": True,
            "when": {"field": "compile_enabled", "op": "eq", "value": True},
        },
    }
    schema = Schema._from_dict(schema_dict)

    with pytest.raises(ValidationError, match="Must be of type int"):
        schema.build_and_validate({"compile_enabled": True, "threads": "not-an-int"}, strict=True)


def test_schema_when_inactive_subsection_is_skipped_in_strict_mode():
    schema_dict = {
        "compile_enabled": {
            "type": "bool",
            "description": "compile toggle",
            "required": False,
            "default": False,
        },
        "compile": {
            "required": False,
            "when": {"field": "compile_enabled", "op": "eq", "value": True},
            "command": {
                "type": "str",
                "description": "compile command",
                "required": True,
            },
        },
    }
    schema = Schema._from_dict(schema_dict)

    built, data_with_default = schema.build_and_validate(
        {"compile": {"command": 123, "extra": "ignored"}},
        strict=True,
    )

    assert built["compile_enabled"] is False
    assert "compile" not in built
    assert "compile" not in data_with_default


def test_schema_when_active_subsection_is_validated():
    schema_dict = {
        "compile_enabled": {
            "type": "bool",
            "description": "compile toggle",
            "required": False,
            "default": False,
        },
        "compile": {
            "required": False,
            "when": {"field": "compile_enabled", "op": "eq", "value": True},
            "command": {
                "type": "str",
                "description": "compile command",
                "required": True,
            },
        },
    }
    schema = Schema._from_dict(schema_dict)

    with pytest.raises(ValidationError, match="Missing required field 'command'"):
        schema.build_and_validate({"compile_enabled": True, "compile": {}}, strict=True)


def test_schema_when_condition_uses_default_value():
    schema_dict = {
        "compile_enabled": {
            "type": "bool",
            "description": "compile toggle",
            "required": False,
            "default": True,
        },
        "compile": {
            "required": True,
            "when": {"field": "compile_enabled", "op": "eq", "value": True},
            "command": {
                "type": "str",
                "description": "compile command",
                "required": True,
            },
        },
    }
    schema = Schema._from_dict(schema_dict)

    with pytest.raises(ValidationError, match="Missing required section 'compile'"):
        schema.build_and_validate({}, strict=True)


def test_schema_rejects_invalid_field_when_definition():
    schema_dict = {
        "threads": {
            "type": "int",
            "description": "thread count",
            "when": {"field": "compile_enabled", "op": "invalid_op", "value": True},
        }
    }

    with pytest.raises(ValidationError, match="unsupported operator"):
        Schema._from_dict(schema_dict)


def test_schema_rejects_invalid_section_when_definition():
    schema_dict = {
        "compile": {
            "required": False,
            "when": {"all": []},
            "command": {
                "type": "str",
                "description": "compile command",
                "required": True,
            },
        }
    }

    with pytest.raises(ValidationError, match="must be a non-empty list"):
        Schema._from_dict(schema_dict)


def test_schema_allows_field_named_when_for_backward_compatibility():
    schema_dict = {
        "when": {
            "type": "int",
            "description": "legacy field name",
            "required": True,
        }
    }
    schema = Schema._from_dict(schema_dict)

    built, _ = schema.build_and_validate({"when": 5}, strict=True)
    assert built["when"] == 5


def test_schema_when_does_not_disable_top_level_strict_unknown_key_check():
    schema_dict = {
        "compile_enabled": {
            "type": "bool",
            "description": "compile toggle",
            "required": False,
            "default": False,
        },
        "compile": {
            "required": False,
            "when": {"field": "compile_enabled", "op": "eq", "value": True},
            "command": {
                "type": "str",
                "description": "compile command",
                "required": True,
            },
        },
    }
    schema = Schema._from_dict(schema_dict)

    with pytest.raises(ValidationError, match="Unexpected key\\(s\\) in section '<root>'"):
        schema.build_and_validate({"unknown": 1}, strict=True)


def test_schema_when_inactive_field_default_is_not_injected_into_condition_context():
    schema_dict = {
        "feature_enabled": {
            "type": "bool",
            "description": "feature toggle",
            "required": False,
            "default": False,
        },
        "hidden_value": {
            "type": "int",
            "description": "hidden default",
            "required": False,
            "default": 42,
            "when": {"field": "feature_enabled", "op": "eq", "value": True},
        },
        "consumer": {
            "type": "str",
            "description": "depends on hidden value presence",
            "required": True,
            "when": {"field": "hidden_value", "op": "exists"},
        },
    }
    schema = Schema._from_dict(schema_dict)

    built, data_with_default = schema.build_and_validate({}, strict=True)

    assert built["feature_enabled"] is False
    assert "hidden_value" not in built
    assert "consumer" not in built
    assert "hidden_value" not in data_with_default
    assert "consumer" not in data_with_default


def test_schema_when_inactive_subsection_default_is_not_injected_into_condition_context():
    schema_dict = {
        "advanced_enabled": {
            "type": "bool",
            "description": "advanced toggle",
            "required": False,
            "default": False,
        },
        "advanced": {
            "required": False,
            "default": {"threshold": 10},
            "when": {"field": "advanced_enabled", "op": "eq", "value": True},
            "threshold": {
                "type": "int",
                "description": "advanced threshold",
                "required": False,
                "default": 10,
            },
        },
        "consumer": {
            "type": "str",
            "description": "depends on advanced threshold",
            "required": True,
            "when": {"field": "advanced.threshold", "op": "exists"},
        },
    }
    schema = Schema._from_dict(schema_dict)

    built, data_with_default = schema.build_and_validate({}, strict=True)

    assert built["advanced_enabled"] is False
    assert "advanced" not in built
    assert "consumer" not in built
    assert "advanced" not in data_with_default
    assert "consumer" not in data_with_default


def test_schema_when_uses_raw_default_values_for_condition_evaluation():
    schema_dict = {
        "pair": {
            "type": "tuple(int, str)",
            "description": "tuple pair",
            "required": False,
            "default": "(1, 'a')",
        },
        "consumer": {
            "type": "str",
            "description": "becomes required when pair raw default matches",
            "required": True,
            "when": {"field": "pair", "op": "eq", "value": "(1, 'a')"},
        },
    }
    schema = Schema._from_dict(schema_dict)

    with pytest.raises(ValidationError, match="Missing required field 'consumer'"):
        schema.build_and_validate({}, strict=True)


def test_schema_without_when_behaves_unchanged():
    schema_dict = {
        "id": {
            "type": "int",
            "description": "identifier",
        },
        "retries": {
            "type": "int",
            "description": "retry count",
            "required": False,
            "default": 3,
        },
    }
    schema = Schema._from_dict(schema_dict)

    built, data_with_default = schema.build_and_validate({"id": 9}, strict=True)
    assert built == {"id": 9, "retries": 3}
    assert data_with_default == {"id": 9, "retries": 3}

    with pytest.raises(ValidationError, match="Missing required field 'id'"):
        schema.build_and_validate({}, strict=True)

