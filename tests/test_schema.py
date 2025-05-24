import pytest

from readtheyaml.fields.field_helpers import _parse_field_type


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
