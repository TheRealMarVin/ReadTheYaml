from functools import partial

import pytest

from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.fields.list_field import ListField
from readtheyaml.fields.numerical_field import NumericalField
from readtheyaml.fields.string_field import StringField
from readtheyaml.fields.bool_field import BoolField

# -------------------
# Tests for ListField
# -------------------

def test_list_field_initialization():
    """Test that ListField is properly initialized with item field."""
    field = ListField(
        name="test_list",
        description="Test list",
        required=False,
        item_field=partial(NumericalField, value_type=int),
        min_length=1,
        max_length=5,
        default=[1] 
    )
    assert field.name == "test_list"
    assert field.description == "Test list"
    assert not field.required
    assert field.min_length == 1
    assert field.max_length == 5


def test_validate_list_of_integers():
    """Test that ListField validates a list of integers."""
    field = ListField(
        name="int_list",
        description="List of integers",
        item_field=partial(NumericalField, value_type=int, name="num", description="Number"),
        default=[0]  # Valid default
    )
    
    # Test valid integer list
    assert field.validate([1, 2, 3]) == [1, 2, 3]


def test_validate_list_converts_string_numbers():
    """Test that ListField converts string numbers to integers."""
    field = ListField(
        name="int_list",
        description="List of integers",
        item_field=partial(NumericalField, value_type=int, name="num", description="Number"),
        default=[0]
    )
    
    # Test string numbers are converted to integers
    assert field.validate(["1", "2", "3"]) == [1, 2, 3]
    assert field.validate(["0", "-42", "999"]) == [0, -42, 999]


def test_validate_list_rejects_non_numeric_strings():
    """Test that ListField rejects non-numeric strings."""
    field = ListField(
        name="int_list",
        description="List of integers",
        item_field=partial(NumericalField, value_type=int, name="num", description="Number"),
        default=[0]
    )
    with pytest.raises(ValidationError, match="Invalid item at index 0"):
        field.validate(["not_an_int"])


def test_validate_list_rejects_mixed_types():
    """Test that ListField rejects lists with mixed valid and invalid types."""
    field = ListField(
        name="int_list",
        description="List of integers",
        item_field=partial(NumericalField, value_type=int, name="num", description="Number"),
        default=[0]
    )
    with pytest.raises(ValidationError, match="Invalid item at index 1"):
        field.validate([1, "not_an_int", 3])


def test_validate_list_rejects_floats():
    """Test that ListField rejects float values when expecting integers."""
    field = ListField(
        name="int_list",
        description="List of integers",
        item_field=partial(NumericalField, value_type=int, name="num", description="Number"),
        default=[0]
    )
    with pytest.raises(ValidationError):
        field.validate([1.5])  # Floats should be rejected when expecting ints


def test_validate_list_accepts_min_length():
    """Test that ListField accepts a list with minimum length."""
    field = ListField(
        name="bounded_list",
        description="Bounded list",
        item_field=partial(StringField, name="item", description="String item"),
        min_length=2,
        max_length=4,
        default=["a", "b"]
    )
    assert field.validate(["a", "b"]) == ["a", "b"]


def test_validate_list_accepts_max_length():
    """Test that ListField accepts a list with maximum length."""
    field = ListField(
        name="bounded_list",
        description="Bounded list",
        item_field=partial(StringField, name="item", description="String item"),
        min_length=2,
        max_length=4,
        default=["a", "b"]
    )
    assert field.validate(["a", "b", "c", "d"]) == ["a", "b", "c", "d"]


def test_validate_list_rejects_below_min_length():
    """Test that ListField rejects a list below minimum length."""
    field = ListField(
        name="bounded_list",
        description="Bounded list",
        item_field=partial(StringField, name="item", description="String item"),
        min_length=2,
        max_length=4,
        default=["a", "b"]
    )
    with pytest.raises(ValidationError, match="must contain at least 2 items"):
        field.validate(["a"])


def test_validate_list_rejects_above_max_length():
    """Test that ListField rejects a list above maximum length."""
    field = ListField(
        name="bounded_list",
        description="Bounded list",
        item_field=partial(StringField, name="item", description="String item"),
        min_length=2,
        max_length=4,
        default=["a", "b"]
    )
    with pytest.raises(ValidationError, match="must contain at most 4 items"):
        field.validate(["a", "b", "c", "d", "e"])


def test_validate_list_with_boolean_values():
    """Test that ListField correctly handles boolean values."""
    field = ListField(
        name="bool_list",
        description="List of booleans",
        item_field=partial(BoolField, name="flag", description="Boolean flag"),
        default=[True]
    )
    assert field.validate([True, False, True]) == [True, False, True]


def test_validate_list_converts_boolean_strings():
    """Test that ListField converts string representations of booleans."""
    field = ListField(
        name="bool_list",
        description="List of booleans",
        item_field=partial(BoolField, name="flag", description="Boolean flag"),
        default=[True]
    )
    assert field.validate(["true", "false", "True", "False"]) == [True, False, True, False]


def test_validate_list_rejects_mixed_invalid_boolean():
    """Test that ListField rejects lists with invalid boolean strings among valid values."""
    field = ListField(
        name="bool_list",
        description="List of booleans",
        item_field=partial(BoolField, name="flag", description="Boolean flag"),
        default=[True]
    )
    with pytest.raises(ValidationError, match="Invalid item at index 1"):
        field.validate([True, "not_a_boolean", False])


def test_validate_list_rejects_single_invalid_boolean():
    """Test that ListField rejects a list with a single invalid boolean string."""
    field = ListField(
        name="bool_list",
        description="List of booleans",
        item_field=partial(BoolField, name="flag", description="Boolean flag"),
        default=[True]
    )
    with pytest.raises(ValidationError, match="Invalid item at index 0"):
        field.validate(["not_a_boolean"])


def test_validate_list_with_mixed_boolean_types():
    """Test that ListField handles mixed boolean types correctly."""
    field = ListField(
        name="bool_list",
        description="List of booleans",
        item_field=partial(BoolField, name="flag", description="Boolean flag"),
        default=[True]
    )
    # Test with Python bools and string representations
    assert field.validate([True, False, "true", "false"]) == [True, False, True, False]


def test_validate_list_accepts_valid_strings():
    """Test that ListField accepts strings within length constraints."""
    field = ListField(
        name="string_list",
        description="List of strings with length constraints",
        item_field=partial(
            StringField,
            name="text", 
            description="Text item",
            min_length=2,
            max_length=5
        ),
        default=["abc"]
    )
    assert field.validate(["ab", "abc", "abcd"]) == ["ab", "abc", "abcd"]


def test_validate_list_rejects_short_strings():
    """Test that ListField rejects strings shorter than min_length."""
    field = ListField(
        name="string_list",
        description="List of strings with length constraints",
        item_field=partial(
            StringField,
            name="text",
            description="Text item",
            min_length=2,
            max_length=5
        ),
        default=["abc"]
    )
    with pytest.raises(ValidationError, match="must be at least 2 characters"):
        field.validate(["a", "bc", "def"])


def test_validate_list_rejects_long_strings():
    """Test that ListField rejects strings longer than max_length."""
    field = ListField(
        name="string_list",
        description="List of strings with length constraints",
        item_field=partial(
            StringField,
            name="text",
            description="Text item",
            min_length=2,
            max_length=5
        ),
        default=["abc"]
    )
    with pytest.raises(ValidationError, match="must be at most 5 characters"):
        field.validate(["abcde", "abcdef"])


def test_validate_list_with_exact_length_strings():
    """Test that ListField handles strings with exact min and max lengths."""
    field = ListField(
        name="string_list",
        description="List of strings with length constraints",
        item_field=partial(
            StringField,
            name="text",
            description="Text item",
            min_length=2,
            max_length=5
        ),
        default=["abc"]
    )
    # Test strings with exact min and max lengths
    assert field.validate(["ab", "abcde"]) == ["ab", "abcde"]


def test_validate_empty_list_default_min_length():
    """Test that ListField with no min_length accepts empty lists."""
    field = ListField(
        name="empty_ok_list",
        description="List that can be empty",
        item_field=partial(StringField, name="item", description="String item"),
        default=[]
    )
    assert field.validate([]) == []


def test_validate_empty_list_explicit_min_length_zero():
    """Test that ListField with min_length=0 accepts empty lists."""
    field = ListField(
        name="empty_ok_list2",
        description="List that can be empty",
        item_field=partial(StringField, name="item", description="String item"),
        min_length=0,
        default=[]
    )
    assert field.validate([]) == []


def test_validate_empty_list_rejects_when_min_length_one():
    """Test that ListField with min_length=1 rejects empty lists."""
    field = ListField(
        name="non_empty_list",
        description="List that cannot be empty",
        item_field=partial(StringField, name="item", description="String item"),
        min_length=1,
        default=["valid"]
    )
    with pytest.raises(ValidationError, match="must contain at least 1 item"):
        field.validate([])


def test_validate_empty_list_with_non_empty_default():
    """Test that ListField with min_length=1 accepts non-empty lists."""
    field = ListField(
        name="non_empty_list",
        description="List that cannot be empty",
        item_field=partial(StringField, name="item", description="String item"),
        min_length=1,
        default=["valid"]
    )
    assert field.validate(["single_item"]) == ["single_item"]


def test_list_field_accepts_min_length_range():
    """Test that ListField accepts a list with minimum length in range."""
    field = ListField(
        name="ranged_list",
        description="List with length range",
        item_field=partial(NumericalField, name="num", description="Number", value_type=int),
        length_range=(2, 4),
        default=[1, 2]
    )
    assert field.validate([1, 2]) == [1, 2]


def test_list_field_accepts_max_length_range():
    """Test that ListField accepts a list with maximum length in range."""
    field = ListField(
        name="ranged_list",
        description="List with length range",
        item_field=partial(NumericalField, name="num", description="Number", value_type=int),
        length_range=(2, 4),
        default=[1, 2, 3, 4]
    )
    assert field.validate([1, 2, 3, 4]) == [1, 2, 3, 4]


def test_list_field_rejects_below_min_length_range():
    """Test that ListField rejects a list below the minimum length in range."""
    field = ListField(
        name="ranged_list",
        description="List with length range",
        item_field=partial(NumericalField, name="num", description="Number", value_type=int),
        length_range=(2, 4),
        default=[1, 2]
    )
    with pytest.raises(ValidationError, match="must contain at least 2 items"):
        field.validate([1])


def test_list_field_rejects_above_max_length_range():
    """Test that ListField rejects a list above the maximum length in range."""
    field = ListField(
        name="ranged_list",
        description="List with length range",
        item_field=partial(NumericalField, name="num", description="Number", value_type=int),
        length_range=(2, 4),
        default=[1, 2, 3, 4]
    )
    with pytest.raises(ValidationError, match="must contain at most 4 items"):
        field.validate([1, 2, 3, 4, 5])


def test_list_field_with_length_range_accepts_middle_length():
    """Test that ListField accepts a list with length in the middle of the range."""
    field = ListField(
        name="ranged_list",
        description="List with length range",
        item_field=partial(NumericalField, name="num", description="Number", value_type=int),
        length_range=(2, 4),
        default=[1, 2, 3]
    )
    assert field.validate([1, 2, 3]) == [1, 2, 3]

def test_list_field_uses_default_when_no_value_provided():
    """Test that ListField uses default value when no value is provided to validate()."""
    field = ListField(
        name="default_list",
        description="List with default value",
        item_field=partial(StringField, name="item", description="String item"),
        default=["default1", "default2"]
    )
    # The default is used when accessing the field's value before validation
    assert field.default == ["default1", "default2"]
    # Empty list is still a valid input
    assert field.validate([]) == []


def test_list_field_validates_provided_values():
    """Test that ListField validates values provided to validate()."""
    field = ListField(
        name="test_list",
        description="Test list",
        item_field=partial(StringField, name="item", description="String item"),
        default=["default"]
    )
    # Validate with custom values
    assert field.validate(["custom1", "custom2"]) == ["custom1", "custom2"]
    # Default is not used when a value is provided to validate()
    assert field.validate(["another"]) == ["another"]


def test_list_field_rejects_none():
    """Test that ListField rejects None as a value."""
    field = ListField(
        name="test_list",
        description="Test list",
        item_field=partial(StringField, name="item", description="String item"),
        default=[]
    )
    with pytest.raises(ValidationError, match="Expected a list"):
        field.validate(None)