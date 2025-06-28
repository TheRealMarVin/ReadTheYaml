

from readtheyaml.exceptions.format_error import FormatError
from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.fields.field_helpers import _parse_field_type, get_reserved_keywords_by_loaded_fields
from readtheyaml.schema import Schema

import os
import pytest
import sys


# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
#
# if project_root not in sys.path:
#     sys.path.insert(0, project_root)
#
class MyDummy:
    pass

# base types
def test_valid_none():
    field = _parse_field_type("None")
    assert field.__name__ == "NoneField"

def test_valid_bool():
    field = _parse_field_type("bool")
    assert field.__name__ == "BoolField"

def test_valid_int():
    field = _parse_field_type("int")
    assert field.func.__name__ == "NumericalField"

def test_valid_float():
    field = _parse_field_type("float")
    assert field.func.__name__ == "NumericalField"

def test_valid_str():
    field = _parse_field_type("str")
    assert field.__name__ == "StringField"

# Union
def test_valid_union_int_str_pipe():
    field = _parse_field_type("int | str")
    assert field.func.__name__ == "UnionField"

def test_valid_union_int_str_fct_round_bracket():
    field = _parse_field_type("union(int, str)")
    assert field.func.__name__ == "UnionField"

def test_valid_union_int_direct_object():
    field = _parse_field_type("union(int, tests.test_schema.MyDummy)")
    assert field.func.__name__ == "UnionField"

def test_valid_union_int_object():
    field = _parse_field_type("union(int, object[tests.test_schema.MyDummy])")
    assert field.func.__name__ == "UnionField"

def test_valid_union_int_str_fct_square_bracket():
    field = _parse_field_type("union[int, str]")
    assert field.func.__name__ == "UnionField"

def test_invalid_union_bracket_mix():
    with pytest.raises(ValueError, match="Mismatched brackets"):
        _parse_field_type("union[int, None)")

    with pytest.raises(ValueError, match="Mismatched brackets"):
        _parse_field_type("union(str, int]")

def test_invalid_union_one_side():
    with pytest.raises(ValueError, match="Unknown field type"):
        _parse_field_type("int|")

    with pytest.raises(ValueError, match="Unknown field type"):
        _parse_field_type("|int")

# List
def test_valid_list_int_square_brackets():
    field = _parse_field_type("list[int]")
    assert field.func.__name__ == "ListField"

def test_valid_list_float_square_brackets():
    field = _parse_field_type("list[float]")
    assert field.func.__name__ == "ListField"

def test_valid_list_str_square_brackets():
    field = _parse_field_type("list[str]")
    assert field.func.__name__ == "ListField"

def test_valid_tuple_round_brackets():
    field = _parse_field_type("list(int)")
    assert field.func.__name__ == "ListField"

def test_invalid_list_bracket_mix():
    with pytest.raises(ValueError, match="Mismatched brackets"):
        _parse_field_type("list[int)")

    with pytest.raises(ValueError, match="Mismatched brackets"):
        _parse_field_type("list(str]")

def test_list_of_custom_class_parses_correctly():
    """list[MyDummy] should parse incorrectly because it is not in the object tag."""
    field = _parse_field_type("list[tests.test_schema.MyDummy]")

def test_list_of_objects():
    """list[object[MyDummy]] should parse correctly if MyDummy is in scope."""
    field = _parse_field_type("list[object[readtheyaml.tests.test_schema.MyDummy]]")

def test_list_no_type():
    with pytest.raises(ValueError, match="Unknown field type"):
        field = _parse_field_type("list()")

def test_list_two_type():
    with pytest.raises(ValueError, match="Unknown field type"):
        _parse_field_type("list(int, float)")

def test_list_union_type():
    field = _parse_field_type("list(int | float)")
    assert field.func.__name__ == "ListField"

# Tuples
def test_valid_tuple_square_brackets():
    field = _parse_field_type("tuple[int, str]")
    assert field.func.__name__ == "TupleField"

def test_valid_tuple_direct_object_square_brackets():
    field = _parse_field_type("tuple[int, tests.test_schema.MyDummy]")
    assert field.func.__name__ == "TupleField"

def test_valid_tuple_object_square_brackets():
    field = _parse_field_type("tuple[int, object[tests.test_schema.MyDummy]]")
    assert field.func.__name__ == "TupleField"

def test_valid_tuple_round_brackets():
    field = _parse_field_type("tuple(int, str)")
    assert field.func.__name__ == "TupleField"


def test_valid_tuple_direct_object_round_brackets():
    field = _parse_field_type("tuple(int, tests.test_schema.MyDummy)")
    assert field.func.__name__ == "TupleField"


def test_valid_tuple_object_round_brackets():
    field = _parse_field_type("tuple(int, object[tests.test_schema.MyDummy])")
    assert field.func.__name__ == "TupleField"

def test_invalid_tuple_bracket_mix():
    with pytest.raises(ValueError, match="Mismatched brackets"):
        _parse_field_type("tuple[int, str)")

    with pytest.raises(ValueError, match="Mismatched brackets"):
        _parse_field_type("tuple(int, str]")

# -------------------
# Tests Objects
# -------------------
def test_valid_any_object_square_brackets():
    field = _parse_field_type("object[*]")
    assert field.func.__name__ == "ObjectField"

def test_valid_any_object_round_brackets():
    field = _parse_field_type("object(*)")
    assert field.func.__name__ == "ObjectField"

def test_valid_direct_object():
    # At this stage we don't care if the type is not valid. It should be raised by the factory.
    # Now we are only parsing.
    field = _parse_field_type("tests.test_schema.MyDummy")
    assert field.func.__name__ == "ObjectField"

def test_valid_object_square_brackets():
    # At this stage we don't care if the type is not valid. It should be raised by the factory.
    # Now we are only parsing.
    field = _parse_field_type("object[tests.test_schema.MyDummy]")
    assert field.func.__name__ == "ObjectField"

def test_valid_object_round_brackets():
    # At this stage we don't care if the type is not valid. It should be raised by the factory.
    # Now we are only parsing.
    field = _parse_field_type("object(tests.test_schema.MyDummy)")
    assert field.func.__name__ == "ObjectField"

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

