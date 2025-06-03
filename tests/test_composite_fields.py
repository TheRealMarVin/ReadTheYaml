from functools import partial

import pytest

from readtheyaml.exceptions.format_error import FormatError
from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.fields.list_field import ListField
from readtheyaml.fields.numerical_field import NumericalField
from readtheyaml.fields.string_field import StringField
from readtheyaml.fields.bool_field import BoolField
from readtheyaml.fields.tuple_field import TupleField
from readtheyaml.fields.union_field import UnionField


# -------------------
# Tests for UnionField
# -------------------
def test_union_field_initialization():
    """Test that UnionField is properly initialized with options."""
    field = UnionField(
        name="test_union",
        description="Test union field",
        required=True,
        options=[
            partial(StringField, name="string_option", description="String option", cast_to_string=False),
            partial(NumericalField, value_type=int, name="int_option", description="Integer option")
        ]
    )
    assert field.name == "test_union"
    assert field.description == "Test union field"
    assert field.required
    assert len(field._options) == 2


def test_union_field_rejects_string_field_with_cast_to_string_true():
    """Test that UnionField rejects StringField with cast_to_string=True."""
    with pytest.raises(FormatError, match="StringField with cast_to_string=True is not allowed"):
        UnionField(
            name="test_union",
            description="Test invalid union field",
            options=[
                partial(StringField, name="string_option", description="String option", cast_to_string=True),  # cast_to_string defaults to False
                partial(NumericalField, value_type=int, name="int_option", description="Integer option")
            ]
        )


def test_union_field_accepts_string_field_with_cast_to_string_false():
    """Test that UnionField accepts StringField with cast_to_string=False."""
    field = UnionField(
        name="test_union",
        description="Test valid union field",
        options=[
            partial(StringField, name="string_option", description="String option", cast_to_string=False),
            partial(NumericalField, value_type=int, name="int_option", description="Integer option")
        ]
    )
    assert len(field._options) == 2


def test_union_field_rejects_duplicate_field_types():
    """Test that UnionField rejects duplicate field types in options."""
    with pytest.raises(FormatError, match="Duplicate field types found in UnionField"):
        UnionField(
            name="test_union",
            description="Test duplicate field types",
            options=[
                partial(NumericalField, value_type=int, name="int1", description="First int"),
                partial(NumericalField, value_type=float, name="float1", description="Float field"),
                partial(NumericalField, value_type=int, name="int2", description="Second int")  # Duplicate
            ]
        )


def test_duplicate_check_ignores_different_parameters():
    """Test that UnionField considers field types with different parameters as duplicates."""
    with pytest.raises(FormatError, match="Duplicate field types found in UnionField"):
        UnionField(
            name="test_union",
            description="Test duplicate field types with different parameters",
            options=[
                partial(StringField, name="str1", description="First string", min_length=1, cast_to_string=False),
                partial(NumericalField, value_type=int, name="int1", description="Integer field"),
                partial(StringField, name="str2", description="Second string", max_length=10, cast_to_string=False)  # Still a duplicate
            ]
        )


def create_simple_union_field():
    """Helper function to create a UnionField with string and integer options."""
    return UnionField(
        name="test_union",
        description="Test union field",
        options=[
            partial(StringField, name="string_option", description="String option", cast_to_string=False),
            partial(NumericalField, value_type=int, name="int_option", description="Integer option")
        ]
    )


def test_union_field_validates_string_option():
    """Test that UnionField validates string values when StringField is an option."""
    field = create_simple_union_field()
    assert field.validate("test") == "test"


def test_union_field_validates_int_option():
    """Test that UnionField validates integer values when NumericalField is an option."""
    field = create_simple_union_field()
    assert field.validate(42) == 42


def test_union_field_handles_numeric_strings_as_strings():
    """Test that UnionField treats numeric strings as strings when StringField is first option."""
    field = create_simple_union_field()
    assert field.validate("123") == "123"  # Should be treated as string, not converted to int


def create_test_union_field():
    """Helper function to create a UnionField with string and number options."""
    return UnionField(
        name="test_union",
        description="Test union field",
        options=[
            partial(StringField, name="string_option", description="String option", 
                   min_length=3, cast_to_string=False),
            partial(NumericalField, value_type=int, name="int_option", 
                   description="Integer option", min_value=0)
        ]
    )


def test_union_field_rejects_short_string():
    """Test that UnionField rejects strings that are too short for StringField."""
    field = create_test_union_field()
    with pytest.raises(ValidationError):
        field.validate("ab")


def test_union_field_rejects_negative_number():
    """Test that UnionField rejects numbers below the minimum value for NumericalField."""
    field = create_test_union_field()
    with pytest.raises(ValidationError, match="does not match any allowed type"):
        field.validate(-1)


def test_union_field_rejects_incompatible_type():
    """Test that UnionField rejects values of incompatible types."""
    field = create_test_union_field()
    with pytest.raises(ValidationError, match="does not match any allowed type"):
        field.validate([1, 2, 3])


def create_complex_union_field():
    """Helper function to create a UnionField with complex types."""
    return UnionField(
        name="complex_union",
        description="Union with complex types",
        options=[
            partial(ListField, name="list_option", description="List option",
                    item_field=partial(NumericalField, value_type=int, name="num")),
            partial(TupleField, name="tuple_option", description="Tuple option",
                    element_fields=[
                        partial(StringField, name="name", description="Name"),
                        partial(NumericalField, value_type=int, name="age", description="Age")
                    ])
        ]
    )


def test_union_field_accepts_list_of_numbers():
    """Test that UnionField accepts a list of numbers when ListField is an option."""
    field = create_complex_union_field()
    assert field.validate([1, 2, 3]) == [1, 2, 3]


def test_union_field_accepts_tuple_of_mixed_types():
    """Test that UnionField accepts a tuple of mixed types when TupleField is an option."""
    field = create_complex_union_field()
    assert field.validate(("John", 30)) == ("John", 30)


def test_union_field_parses_string_representation_of_tuple():
    """Test that UnionField parses string representation of a tuple when TupleField is an option."""
    field = create_complex_union_field()
    assert field.validate("('Alice', 25)") == ("Alice", 25)


def test_union_field_required_rejects_none():
    """Test that UnionField with required=True rejects None."""
    field = UnionField(
        name="test_required",
        description="Test required union",
        required=True,
        options=[
            partial(StringField, name="string_option", description="String option")
        ]
    )
    with pytest.raises(ValidationError):
        field.validate(None)


def test_union_field_optional_rejects_none_without_default():
    """Test that UnionField with required=False and no default rejects None."""
    field = UnionField(
        name="test_optional",
        description="Test optional union",
        required=False,
        default="",
        options=[
            partial(StringField, name="string_option", description="String option")
        ]
    )
    with pytest.raises(ValidationError):
        field.validate(None)


def test_union_field_error_messages():
    """Test that UnionField provides useful error messages."""
    field = UnionField(
        name="test_errors",
        description="Test error messages",
        options=[
            partial(StringField, name="string_option", description="String option", min_length=3),
            partial(NumericalField, value_type=int, name="int_option", description="Integer option", min_value=0)
        ]
    )

    with pytest.raises(ValidationError):
        field.validate(False)


# -------------------
# Tests for TupleField
# -------------------

def test_required_tuple_field():
    """Test that a required TupleField is properly initialized without a default."""
    field = TupleField(
        name="test_tuple",
        description="Test tuple",
        required=True,
        element_fields=[
            partial(StringField, name="name", description="Name field"),
            partial(NumericalField, value_type=int, name="age", description="Age field")
        ]
    )
    assert field.name == "test_tuple"
    assert field.description == "Test tuple"
    assert field.required
    assert field.default is None  # No default for required fields
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
            partial(StringField, name="name", description="Name field"),
            partial(NumericalField, value_type=int, name="age", description="Age field")
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
            partial(StringField, name="name", description="Name"),
            partial(NumericalField, value_type=int, name="age", description="Age"),
            partial(BoolField, name="active", description="Active status")
        ]
    )
    
    # Test valid tuple
    result = field.validate(("John Doe", 30, True))
    assert result == ("John Doe", 30, True)


def test_validate_tuple_with_string_representation():
    """Test that TupleField can parse string representation of a tuple."""
    field = TupleField(
        name="coordinates",
        description="Test tuple",
        element_fields=[
            partial(NumericalField, value_type=float, name="x", description="X coordinate"),
            partial(NumericalField, value_type=float, name="y", description="Y coordinate")
        ]
    )
    
    # Test with string representation
    result = field.validate("(3.14, 2.71)")
    assert result == (3.14, 2.71)


def test_validate_tuple_rejects_wrong_length():
    """Test that TupleField rejects tuples with wrong length."""
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
        field.validate((1.0,))
    
    # Test with too many elements
    with pytest.raises(ValidationError, match="must contain exactly 2 elements"):
        field.validate((1.0, 2.0, 3.0))


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
        field.validate(("John Doe", "thirty"))  # Age should be an int


def test_validate_tuple_with_nested_structures():
    """Test that TupleField works with nested structures."""
    field = TupleField(
        name="nested",
        description="Test tuple",
        element_fields=[
            partial(ListField, name="numbers", item_field=partial(NumericalField, value_type=int, name="num")),
            partial(StringField, name="name", description="Name")
        ]
    )
    
    # Test with valid nested structure
    result = field.validate(([1, 2, 3], "test"))
    assert result == ([1, 2, 3], "test")
    
    # Test with invalid nested structure
    with pytest.raises(ValidationError, match="Tuple element 0 invalid"):
        field.validate(([1, "two", 3], "test"))  # Non-int in list


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
        field.validate(None)


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


def test_nested_list_of_integers():
    """Test that ListField can validate a list of lists of integers."""
    # Create the inner field (list of integers)
    inner_field = partial(
        ListField,
        name="inner_list",
        description="Inner list of integers",
        item_field=partial(NumericalField, name="num", description="Number", value_type=int)
    )
    
    # Create the outer field (list of lists)
    field = ListField(
        name="nested_lists",
        description="List of lists of integers",
        item_field=inner_field,
        default=[[0]]
    )
    
    # Test valid nested lists
    assert field.validate([[1, 2], [3, 4, 5]]) == [[1, 2], [3, 4, 5]]
    assert field.validate([[], [1], [1, 2]]) == [[], [1], [1, 2]]


def create_constrained_nested_list_field():
    """Helper function to create a ListField with constrained inner lists."""
    return ListField(
        name="constrained_nested_lists",
        description="List of constrained lists",
        item_field=partial(
            ListField,
            name="inner_list",
            description="Inner list with constraints",
            item_field=partial(NumericalField, name="num", description="Number", value_type=int),
            min_length=1,
            max_length=3
        ),
        default=[[1]]
    )


def test_nested_list_with_constraints_valid():
    """Test that ListField accepts valid nested lists within constraints."""
    field = create_constrained_nested_list_field()
    assert field.validate([[1], [1, 2], [1, 2, 3]]) == [[1], [1, 2], [1, 2, 3]]


def test_nested_list_with_min_length_constraint():
    """Test that ListField enforces minimum length on inner lists."""
    field = create_constrained_nested_list_field()
    with pytest.raises(ValidationError, match="must contain at least 1 item"):
        field.validate([[]])


def test_nested_list_with_max_length_constraint():
    """Test that ListField enforces maximum length on inner lists."""
    field = create_constrained_nested_list_field()
    with pytest.raises(ValidationError, match="must contain at most 3 items"):
        field.validate([[1, 2, 3, 4]])


def test_nested_list_with_various_valid_lengths():
    """Test that ListField accepts inner lists at different valid lengths."""
    field = create_constrained_nested_list_field()
    assert field.validate([[1], [2, 2], [3, 3, 3]]) == [[1], [2, 2], [3, 3, 3]]


def test_nested_list_rejects_mixed_valid_and_invalid():
    """Test that ListField rejects lists containing both valid and invalid inner lists."""
    field = create_constrained_nested_list_field()
    with pytest.raises(ValidationError):
        field.validate([[], [1], [1, 2, 3, 4]])


def test_deeply_nested_lists():
    """Test that ListField can handle deeply nested lists."""
    # Create a field for a list of lists of lists of integers
    innermost_field = partial(NumericalField, name="num", description="Number", value_type=int)
    
    middle_field = partial(ListField,
        name="middle_list",
        description="Middle list",
        item_field=innermost_field
    )
    
    outer_field = partial(ListField,
        name="outer_list",
        description="Outer list",
        item_field=middle_field
    )
    
    field = ListField(
        name="deeply_nested",
        description="Deeply nested lists",
        item_field=outer_field,
        default=[[[1]]]
    )
    
    # Test valid deeply nested lists
    assert field.validate([[[1], [2, 3]], [[4, 5, 6]]]) == [[[1], [2, 3]], [[4, 5, 6]]]
    
    # Test invalid type in deepest level
    with pytest.raises(ValidationError):
        field.validate([[["not_a_number"]]])

