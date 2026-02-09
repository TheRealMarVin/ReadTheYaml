

from readtheyaml.exceptions.format_error import FormatError
from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.fields.field_helpers import get_reserved_keywords_by_loaded_fields
from readtheyaml.schema import Schema

import os
import pytest
import sys


class MyDummy:
    pass

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
    """Optional subsection should not raise if missing and should produce defaults."""
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

    assert "optional_section" in built
    assert built["optional_section"] == {"enabled": False}
    assert data_with_default["optional_section"]["enabled"] is False

