import pytest

from readtheyaml.exceptions.format_error import FormatError
from readtheyaml.fields.field_helpers import _parse_field_type, get_reserved_keywords_by_loaded_fields
from readtheyaml.schema import Schema


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

def test_list_unknown_type():
    with pytest.raises(ValueError, match="Unknown field type: foo"):
        _parse_field_type("list[foo]")

def test_list_no_type():
    with pytest.raises(ValueError, match="Unknown field type: list()"):
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

def test_valid_tuple_round_brackets():
    field = _parse_field_type("tuple(int, str)")
    assert field.func.__name__ == "TupleField"

def test_invalid_tuple_bracket_mix():
    with pytest.raises(ValueError, match="Mismatched brackets"):
        _parse_field_type("tuple[int, str)")

    with pytest.raises(ValueError, match="Mismatched brackets"):
        _parse_field_type("tuple(int, str]")

def test_tuple_unknown_type():
    with pytest.raises(ValueError, match="Unknown field type: foo"):
        _parse_field_type("tuple[foo, str]")

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
