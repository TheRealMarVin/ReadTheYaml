from functools import partial

import pytest

from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.fields.composite.list_field import ListField
from readtheyaml.fields.base.numerical_field import NumericalField
from readtheyaml.fields.base.string_field import StringField
from readtheyaml.fields.base.bool_field import BoolField
from readtheyaml.fields.composite.tuple_field import TupleField


def test_required_tuple_field():
    """Test that a required TupleField is properly initialized without a default."""
    field = TupleField(
        name="test_tuple",
        description="Test tuple",
        required=True,
        element_fields=[
            partial(StringField),
            partial(NumericalField, value_type=int)
        ]
    )
    assert field.name == "test_tuple"
    assert field.description == "Test tuple"
    assert field.required
    assert field.default is None
    assert len(field._slots) == 2


def test_optional_tuple_field_with_default():
    """Test that an optional TupleField can be initialized with a default value."""
    default_value = ("John", 30)
    field = TupleField(
        name="test_tuple",
        description="Test tuple",
        required=False,
        default=default_value,
        element_fields=[
            partial(StringField),
            partial(NumericalField, value_type=int)
        ]
    )
    assert field.name == "test_tuple"
    assert field.description == "Test tuple"
    assert not field.required
    assert field.default == default_value
    assert len(field._slots) == 2


def test_validate_tuple_with_correct_types():
    """Test that TupleField validates a tuple with correct types."""
    field = TupleField(
        name="person",
        description="Test tuple",
        element_fields=[
            partial(StringField),
            partial(NumericalField, value_type=int),
            partial(BoolField)
        ]
    )

    # Test valid tuple
    result = field.validate_and_build(("John Doe", 30, True))
    assert result == ("John Doe", 30, True)


def test_validate_tuple_with_string_representation():
    """Test that TupleField can parse a string representation of a tuple."""
    field = TupleField(
        name="coordinates",
        description="Test tuple",
        element_fields=[
            partial(NumericalField, value_type=float, name="x", description="X coordinate"),
            partial(NumericalField, value_type=float, name="y", description="Y coordinate")
        ]
    )

    # Test with string representation
    result = field.validate_and_build("(3.14, 2.71)")
    assert result == (3.14, 2.71)


def test_validate_tuple_rejects_wrong_length():
    """Test that TupleField rejects tuples with the wrong length."""
    field = TupleField(
        name="coordinates",
        description="Test tuple",
        element_fields=[
            partial(NumericalField, value_type=float, name="x", description="X coordinate"),
            partial(NumericalField, value_type=float, name="y", description="Y coordinate")
        ]
    )

    # Test with too few elements
    with pytest.raises(ValidationError, match="must contain exactly 2 elements"):
        field.validate_and_build((1.0,))

    # Test with too many elements
    with pytest.raises(ValidationError, match="must contain exactly 2 elements"):
        field.validate_and_build((1.0, 2.0, 3.0))


def test_validate_tuple_rejects_invalid_types():
    """Test that TupleField rejects elements with invalid types."""
    field = TupleField(
        name="person",
        description="Test tuple",
        element_fields=[
            partial(StringField, name="name", description="Name"),
            partial(NumericalField, value_type=int, name="age", description="Age")
        ]
    )

    # Test with invalid type in second element
    with pytest.raises(ValidationError, match="Tuple element 1 invalid"):
        field.validate_and_build(("John Doe", "thirty"))  # Age should be an int


def test_validate_tuple_with_nested_structures():
    """Test that TupleField works with nested structures."""
    field = TupleField(
        name="nested",
        description="Test tuple",
        element_fields=[
            partial(ListField, name="numbers", description="numbers",
                    item_field=partial(NumericalField, value_type=int, name="num", description="Val")),
            partial(StringField, name="name", description="Name", cast_to_string=False)
        ]
    )

    # Test with a valid nested structure
    result = field.validate_and_build(([1, 2, 3], "test"))
    assert result == ([1, 2, 3], "test")

    # Test with an invalid nested structure
    with pytest.raises(ValidationError, match="Tuple element 0 invalid"):
        field.validate_and_build(([1, "two", 3], "test"))  # Non-int in a list


def test_validate_tuple_rejects_none():
    """Test that TupleField rejects None as a value."""
    field = TupleField(
        name="test",
        description="Test tuple",
        element_fields=[
            partial(StringField, name="name", description="Name")
        ]
    )

    with pytest.raises(ValidationError, match="None is not a valid tuple"):
        field.validate_and_build(None)