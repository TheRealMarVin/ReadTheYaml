import sys
import pytest
from decimal import Decimal
from fractions import Fraction

from readtheyaml.exceptions.format_error import FormatError
from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.fields.bool_field import BoolField
from readtheyaml.fields.none_field import NoneField
from readtheyaml.fields.numerical_field import NumericalField
from readtheyaml.fields.string_field import StringField


# -------------------
# Tests for NoneField
# -------------------
def test_none_field_initialization():
    """Test that NoneField is properly initialized."""
    field = NoneField(name="new_field", description="My description", required=False, default=None)
    assert field.name == "new_field"
    assert field.description == "My description"
    assert not field.required

def test_none_field_validate_uppercase_none():
    """Test validation of string 'None' as None."""
    field = NoneField(name="new_field", description="My description", required=False, default=None)
    assert field.validate("None") is None

def test_none_field_validate_lowercase_none():
    """Test validation of string 'none' as None."""
    field = NoneField(name="new_field", description="My description", required=False, default=None)
    assert field.validate("none") is None

def test_none_field_validate_actual_none():
    """Test validation of actual None value."""
    field = NoneField(name="new_field", description="My description", required=False, default=None)
    assert field.validate(None) is None

def test_none_field_rejects_empty_string():
    """Test rejection of empty string input."""
    field = NoneField(name="new_field", description="My description", required=False, default=None)
    with pytest.raises(ValidationError, match="must be null/None"):
        field.validate("")

def test_none_field_rejects_numeric_string():
    """Test rejection of numeric string input."""
    field = NoneField(name="new_field", description="My description", required=False, default=None)
    with pytest.raises(ValidationError, match="must be null/None"):
        field.validate("123")

def test_none_field_rejects_integer():
    """Test rejection of integer input."""
    field = NoneField(name="new_field", description="My description", required=False, default=None)
    with pytest.raises(ValidationError, match="must be null/None"):
        field.validate(123)

def test_none_field_accepts_string_default():
    """Test field initialization with string 'None' as default."""
    field = NoneField(name="new_field", description="My description", required=False, default="None")
    assert field.default == "None"

def test_none_field_rejects_bool_default():
    """Test that boolean default value raises FormatError."""
    with pytest.raises(FormatError, match="invalid default value"):
        NoneField(name="new_field", description="My description", required=False, default=True)

def test_none_field_rejects_zero_default():
    """Test that integer zero default value raises FormatError."""
    with pytest.raises(FormatError, match="invalid default value"):
        NoneField(name="new_field", description="My description", required=False, default=0)

def test_none_field_rejects_string_default():
    """Test that arbitrary string default value raises FormatError."""
    with pytest.raises(FormatError, match="invalid default value"):
        NoneField(name="new_field", description="My description", required=False, default="test")

# testing Bool
def test_validate_bool_true():
    """Test that boolean True values are validated correctly."""
    field = BoolField(name="new_field", description="My description", required=False, default=True)
    assert field.name == "new_field" and field.description == "My description" and not field.required
    
    confirmed_value = field.validate(True)
    assert confirmed_value is True

def test_validate_bool_true_string():
    """Test that string 'True' is converted to boolean True."""
    field = BoolField(name="new_field", description="My description", required=False, default=True)
    confirmed_value = field.validate("True")
    assert confirmed_value is True

def test_validate_bool_false():
    """Test that boolean False values are validated correctly."""
    field = BoolField(name="new_field", description="My description", required=False, default=True)
    confirmed_value = field.validate(False)
    assert confirmed_value is False

def test_validate_bool_false_string():
    """Test that string 'False' is converted to boolean False."""
    field = BoolField(name="new_field", description="My description", required=False, default=True)
    confirmed_value = field.validate("False")
    assert confirmed_value is False

def test_validate_bool_empty_string():
    """Test that empty string raises ValidationError."""
    field = BoolField(name="new_field", description="My description", required=False, default=True)
    with pytest.raises(ValidationError, match="Must be of type bool"):
        field.validate("")

def test_validate_bool_numerical_string():
    """Test that numerical string raises ValidationError."""
    field = BoolField(name="new_field", description="My description", required=False, default=True)
    with pytest.raises(ValidationError, match="Expected a boolean value"):
        field.validate("123")

def test_validate_bool_integer():
    """Test that integer raises ValidationError."""
    field = BoolField(name="new_field", description="My description", required=False, default=True)
    with pytest.raises(ValidationError, match="Expected a boolean value"):
        field.validate(123)

def test_validate_bool_case_insensitive_true():
    """Test that 'true' boolean strings are case-insensitive."""
    field = BoolField(name="new_field", description="Case insensitive true test")
    
    true_variations = [
        "TRUE",  # All uppercase
        "True",  # Title case
        "tRuE",  # Mixed case
        "true"   # All lowercase
    ]
    
    for value in true_variations:
        assert field.validate(value) is True, f"Failed for value: {repr(value)}"

def test_validate_bool_case_insensitive_false():
    """Test that 'false' boolean strings are case-insensitive."""
    field = BoolField(name="new_field", description="Case insensitive false test")
    
    false_variations = [
        "FALSE",  # All uppercase
        "False",  # Title case
        "fAlSe",  # Mixed case
        "false"   # All lowercase
    ]
    
    for value in false_variations:
        assert field.validate(value) is False, f"Failed for value: {repr(value)}"

def test_validate_bool_rejects_leading_trailing_whitespace():
    """Test that boolean strings with leading/trailing whitespace are rejected."""
    field = BoolField(name="new_field", description="Leading/trailing whitespace test")
    
    test_cases = [
        " true ",    # Spaces around
        "\ttrue\n",  # Tabs and newlines
        "  false  "  # Multiple spaces
    ]
    
    for value in test_cases:
        with pytest.raises(ValidationError, match="Expected a boolean value"):
            field.validate(value)

def test_validate_bool_rejects_multiple_whitespace():
    """Test that boolean strings with multiple whitespace characters are rejected."""
    field = BoolField(name="new_field", description="Multiple whitespace test")
    
    test_cases = [
        "  true  ",  # Multiple leading/trailing spaces
        "false  ",    # Trailing spaces
        "  true",     # Leading spaces
        "false\t"     # Trailing tab
    ]
    
    for value in test_cases:
        with pytest.raises(ValidationError, match="Expected a boolean value"):
            field.validate(value)

def test_validate_bool_rejects_alternative_boolean_strings():
    """Test that common alternative boolean strings are rejected."""
    field = BoolField(name="new_field", description="Alternative boolean strings test")
    
    alternative_booleans = ["yes", "no", "on", "off", "1", "0", "y", "n"]
    for value in alternative_booleans:
        with pytest.raises(ValidationError, match="Expected a boolean value"):
            field.validate(value)

def test_validate_bool_rejects_none():
    """Test that None is rejected with the correct error message."""
    field = BoolField(name="new_field", description="None value test")
    with pytest.raises(ValidationError, match="Expected a boolean value, got NoneType"):
        field.validate(None)

def test_validate_bool_none_strings():
    """Test that strings that might be interpreted as None are handled correctly."""
    field = BoolField(name="new_field", description="None string test")
    
    # Test that 'none' and 'null' strings are rejected with appropriate message
    for value in ["none", "None", "NONE", "null", "Null", "NULL"]:
        with pytest.raises(ValidationError, match="contains None or null or empty"):
            field.validate(value)

def test_validate_bool_empty_string():
    """Test that empty string raises ValidationError."""
    field = BoolField(name="new_field", description="Empty string test")
    with pytest.raises(ValidationError, match="Must be of type bool"):
        field.validate("")

def test_bool_field_with_text_default_true():
    """Test that default can be set as string 'True'."""
    field = BoolField(name="new_field", description="My description", required=False, default="True")
    assert field.default is "True"

def test_bool_field_with_text_default_false():
    """Test that default can be set as string 'False'."""
    field = BoolField(name="new_field", description="My description", required=False, default="False")
    assert field.default is "False"

def test_bool_field_invalid_default_none():
    """Test that None as default raises FormatError."""
    with pytest.raises(FormatError, match="invalid default value"):
        BoolField(name="new_field", description="My description", required=False, default=None)

def test_bool_field_invalid_default_zero():
    """Test that 0 as default raises FormatError."""
    with pytest.raises(FormatError, match="invalid default value"):
        BoolField(name="new_field", description="My description", required=False, default=0)

def test_bool_field_invalid_default_float():
    """Test that float as default raises FormatError."""
    with pytest.raises(FormatError, match="invalid default value"):
        BoolField(name="new_field", description="My description", required=False, default=12.5)

def test_bool_field_invalid_default_empty_string():
    """Test that empty string as default raises FormatError."""
    with pytest.raises(FormatError, match="invalid default value"):
        BoolField(name="new_field", description="My description", required=False, default="")

# testing int
def test_validate_int_positive():
    """Test that positive integers are validated correctly."""
    field = NumericalField(name="new_field", description="My description", required=False, default=1,
                          value_type=int, min_value=None, max_value=None, value_range=None)
    assert field.name == "new_field" and field.description == "My description" and not field.required
    assert field.validate(123) == 123

def test_validate_int_string():
    """Test that string representations of integers are converted correctly."""
    field = NumericalField(name="new_field", description="My description", required=False, default=1,
                          value_type=int, min_value=None, max_value=None, value_range=None)
    assert field.validate("123") == 123

def test_validate_int_zero():
    """Test that zero is validated correctly."""
    field = NumericalField(name="new_field", description="My description", required=False, default=1,
                          value_type=int, min_value=None, max_value=None, value_range=None)
    assert field.validate(0) == 0

def test_validate_int_negative():
    """Test that negative integers are validated correctly."""
    field = NumericalField(name="new_field", description="My description", required=False, default=1,
                          value_type=int, min_value=None, max_value=None, value_range=None)
    assert field.validate(-1093257) == -1093257

def test_validate_int_with_min_value():
    """Test that values above min_value are accepted."""
    field = NumericalField(name="new_field", description="My description", required=False, default=15,
                          value_type=int, min_value=10, max_value=None, value_range=None)
    assert field.name == "new_field" and field.description == "My description" and not field.required
    assert field.validate(42) == 42

def test_validate_int_below_min_value():
    """Test that values below min_value raise ValidationError."""
    field = NumericalField(name="new_field", description="My description", required=False, default=15,
                          value_type=int, min_value=10, max_value=None, value_range=None)
    with pytest.raises(ValidationError, match="Value must be at least"):
        field.validate(2)

def test_validate_int_with_max_value():
    """Test that values below max_value are accepted."""
    field = NumericalField(name="new_field", description="My description", required=False, default=1,
                          value_type=int, min_value=None, max_value=512, value_range=None)
    assert field.name == "new_field" and field.description == "My description" and not field.required
    assert field.validate(42) == 42

def test_validate_int_above_max_value():
    """Test that values above max_value raise ValidationError."""
    field = NumericalField(name="new_field", description="My description", required=False, default=1,
                          value_type=int, min_value=None, max_value=512, value_range=None)
    with pytest.raises(ValidationError, match="Value must be at most"):
        field.validate(1024)

def test_validate_int_with_range_array():
    """Test that values within range specified as array are accepted."""
    field = NumericalField(name="new_field", description="My description", required=False, default=15,
                          value_type=int, min_value=None, max_value=None, value_range=[5, 512])
    assert field.name == "new_field" and field.description == "My description" and not field.required
    assert field.validate(42) == 42

def test_validate_int_with_range_tuple():
    """Test that values within range specified as tuple are accepted."""
    field = NumericalField(name="new_field", description="My description", required=False, default=15,
                          value_type=int, min_value=None, max_value=None, value_range=(5, 512))
    assert field.name == "new_field" and field.description == "My description" and not field.required
    assert field.validate(42) == 42

def test_validate_int_with_open_range():
    """Test that values are accepted with open-ended ranges."""
    field = NumericalField(name="new_field", description="My description", required=False, default=1,
                          value_type=int, min_value=None, max_value=None, value_range=[None, None])
    assert field.name == "new_field" and field.description == "My description" and not field.required
    assert field.validate(42) == 42

def test_validate_int_with_min_range():
    """Test that values above minimum range are accepted when only min is specified."""
    field = NumericalField(name="new_field", description="My description", required=False, default=15,
                          value_type=int, min_value=None, max_value=None, value_range=[5, None])
    assert field.name == "new_field" and field.description == "My description" and not field.required
    assert field.validate(42) == 42

def test_validate_int_with_max_range():
    """Test that values below maximum range are accepted when only max is specified."""
    field = NumericalField(name="new_field", description="My description", required=False, default=1,
                          value_type=int, min_value=None, max_value=None, value_range=[None, 512])
    assert field.name == "new_field" and field.description == "My description" and not field.required
    assert field.validate(42) == 42

def test_validate_int_below_min_range():
    """Test that values below minimum range raise ValidationError."""
    field = NumericalField(name="new_field", description="My description", required=False, default=15,
                          value_type=int, min_value=None, max_value=None, value_range=(5, 512))
    with pytest.raises(ValidationError, match="Value must be at least"):
        field.validate(1)

def test_validate_int_above_max_range():
    """Test that values above maximum range raise ValidationError."""
    field = NumericalField(name="new_field", description="My description", required=False, default=15,
                          value_type=int, min_value=None, max_value=None, value_range=(5, 512))
    with pytest.raises(ValidationError, match="Value must be at most"):
        field.validate(1024)

def test_invalid_range_not_enough_values():
    """Test that range with insufficient values raises ValidationError."""
    with pytest.raises(ValidationError, match="Range must have 2 values, 1 provided"):
        NumericalField(name="new_field", description="My description", required=False, default=1,
                      value_type=int, min_value=None, max_value=None, value_range=[None])

def test_invalid_range_too_many_values():
    """Test that range with too many values raises ValidationError."""
    with pytest.raises(ValidationError, match="Range must have 2 values, 3 provided"):
        NumericalField(name="new_field", description="My description", required=False, default=1,
                      value_type=int, min_value=None, max_value=None, value_range=[None, None, None])

def test_invalid_min_greater_than_max():
    """Test that min_value > max_value raises ValidationError."""
    with pytest.raises(ValidationError, match="Minimal value greater than maximal value"):
        NumericalField(name="new_field", description="My description", required=False, default=1,
                     value_type=int, min_value=512, max_value=5, value_range=None)

def test_invalid_float_lower_bound():
    """Test that float min_value with int type raises ValidationError."""
    with pytest.raises(ValidationError, match="is not of type of the field"):
        NumericalField(name="new_field", description="My description", required=False, default=1,
                     value_type=int, min_value=5.2, max_value=None, value_range=None)

def test_invalid_float_upper_bound():
    """Test that float max_value with int type raises ValidationError."""
    with pytest.raises(ValidationError, match="is not of type of the field"):
        NumericalField(name="new_field", description="My description", required=False, default=1,
                     value_type=int, min_value=None, max_value=512.5, value_range=None)

def test_validate_consistent_bounds():
    """Test that consistent min_value, max_value, and value_range are accepted."""
    field = NumericalField(name="new_field", description="My description", required=False, default=10,
                          value_type=int, min_value=5, max_value=512, value_range=(5, 512))
    assert field.name == "new_field" and field.description == "My description" and not field.required
    assert field.validate(42) == 42

def test_invalid_min_and_range_combination():
    """Test that min_value and value_range together raise ValidationError."""
    with pytest.raises(ValidationError, match="using range and lower bound"):
        NumericalField(name="new_field", description="My description", required=False, default=1,
                     value_type=int, min_value=5, max_value=None, value_range=(5, 512))

def test_invalid_max_and_range_combination():
    """Test that max_value and value_range together raise ValidationError."""
    with pytest.raises(ValidationError, match="using range and upper bound"):
        NumericalField(name="new_field", description="My description", required=False, default=1,
                     value_type=int, min_value=None, max_value=512, value_range=(5, 512))

def test_invalid_min_not_matching_range():
    """Test that min_value must match range lower bound when both are provided."""
    with pytest.raises(ValidationError, match="Lower bound value is not matching"):
        NumericalField(name="new_field", description="My description", required=False, default=1,
                     value_type=int, min_value=1, max_value=512, value_range=(5, 512))

def test_invalid_max_not_matching_range():
    """Test that max_value must match range upper bound when both are provided."""
    with pytest.raises(ValidationError, match="Upper bound value is not matching"):
        NumericalField(name="new_field", description="My description", required=False, default=1,
                     value_type=int, min_value=5, max_value=1024, value_range=(5, 512))

def test_validate_int_rejects_none():
    """Test that None is rejected for non-required int fields."""
    field = NumericalField(name="new_field", description="My description", required=False, default=1,
                          value_type=int, min_value=None, max_value=None, value_range=None)
    with pytest.raises(ValidationError, match="Must be of type int"):
        field.validate(None)

def test_validate_int_rejects_string():
    """Test that non-numeric strings are rejected for int fields."""
    field = NumericalField(name="new_field", description="My description", required=False, default=1,
                          value_type=int, min_value=None, max_value=None, value_range=None)
    with pytest.raises(ValidationError, match="Must be of type int"):
        field.validate("str")

def test_validate_int_accepts_numeric_string_default():
    """Test that numeric strings are accepted as default values."""
    field = NumericalField(name="new_field", description="My description", required=False, default="0")
    assert field.name == "new_field" and field.description == "My description" and not field.required
    assert field.validate(0) == 0  # Default should be converted to int

def test_invalid_default_none():
    """Test that None is not a valid default value."""
    with pytest.raises(FormatError, match="invalid default value"):
        NumericalField(name="new_field", description="My description", required=False, default=None)

def test_invalid_default_bool():
    """Test that boolean is not a valid default value."""
    with pytest.raises(FormatError, match="invalid default value"):
        NumericalField(name="new_field", description="My description", required=False, default=True)

def test_invalid_default_float():
    """Test that float is not a valid default value for int field."""
    with pytest.raises(FormatError, match="invalid default value"):
        NumericalField(name="new_field", description="My description", required=False, default=12.5)

def test_invalid_default_empty_string():
    """Test that empty string is not a valid default value."""
    with pytest.raises(FormatError, match="invalid default value"):
        NumericalField(name="new_field", description="My description", required=False, default="")

def test_invalid_default_below_min():
    """Test that default value cannot be below min_value."""
    with pytest.raises(FormatError, match="invalid default value"):
        NumericalField(name="new_field", description="My description", required=False, default=1,
                     value_type=int, min_value=5, max_value=None, value_range=None)

def test_invalid_default_below_range():
    """Test that default value cannot be below range minimum."""
    with pytest.raises(FormatError, match="invalid default value"):
        NumericalField(name="new_field", description="My description", required=False, default=1,
                     value_type=int, min_value=None, max_value=None, value_range=[5, 1024])

def test_invalid_default_above_max():
    """Test that default value cannot be above max_value."""
    with pytest.raises(FormatError, match="invalid default value"):
        NumericalField(name="new_field", description="My description", required=False, default=1024,
                     value_type=int, min_value=None, max_value=512, value_range=None)

def test_invalid_default_above_range():
    """Test that default value cannot be above range maximum."""
    with pytest.raises(FormatError, match="invalid default value"):
        NumericalField(name="new_field", description="My description", required=False, default=2048,
                     value_type=int, min_value=None, max_value=None, value_range=[5, 1024])

def test_validate_float_positive():
    """Test that positive float values are validated correctly."""
    field = NumericalField(name="new_field", description="My description", required=False, default=1.0,
                          value_type=float, min_value=None, max_value=None, value_range=None)
    assert field.validate(123.0) == 123.0

def test_validate_float_from_string():
    """Test that string representations of floats are converted and validated."""
    field = NumericalField(name="new_field", description="My description", required=False, default=1.0,
                          value_type=float)
    assert field.validate("123.5") == 123.5

def test_validate_float_zero():
    """Test that zero values are handled correctly."""
    field = NumericalField(name="new_field", description="My description", required=False, default=1.0,
                          value_type=float)
    assert field.validate(0.0) == 0.0
    assert field.validate(0) == 0.0  # Integer zero should be converted to float

def test_validate_float_negative():
    """Test that negative float values are validated correctly."""
    field = NumericalField(name="new_field", description="My description", required=False, default=1.0,
                          value_type=float)
    assert field.validate(-1093257.2) == -1093257.2

def test_validate_float_above_min():
    """Test that values above minimum are accepted."""
    field = NumericalField(name="new_field", description="My description", required=False, default=15.0,
                          value_type=float, min_value=10.0)
    assert field.validate(42.0) == 42.0
    assert field.validate(10.01) == 10.01  # Just above minimum

def test_validate_float_at_min_boundary():
    """Test that values at minimum boundary are accepted."""
    field = NumericalField(name="new_field", description="My description", required=False, default=10.0,
                          value_type=float, min_value=10.0)
    assert field.validate(10.0) == 10.0

def test_validate_float_below_min():
    """Test that values below minimum raise ValidationError."""
    field = NumericalField(name="new_field", description="My description", required=False, default=15.0,
                          value_type=float, min_value=10.0)
    with pytest.raises(ValidationError, match="Value must be at least"):
        field.validate(2.2)

def test_validate_float_below_max():
    """Test that values below maximum are accepted."""
    field = NumericalField(name="new_field", description="My description", required=False, default=1.0,
                          value_type=float, max_value=512.0)
    assert field.validate(42.1) == 42.1

def test_validate_float_above_max():
    """Test that values above maximum raise ValidationError."""
    field = NumericalField(name="new_field", description="My description", required=False, default=1.0,
                          value_type=float, max_value=512.0)
    with pytest.raises(ValidationError, match="Value must be at most"):
        field.validate(1024.5)

def test_validate_float_with_array_range():
    """Test that values within array range are accepted."""
    field = NumericalField(name="new_field", description="My description", required=False, default=15.0,
                          value_type=float, value_range=[5.0, 512.0])
    assert field.validate(42.0) == 42.0

def test_validate_float_with_tuple_range():
    """Test that values within tuple range are accepted."""
    field = NumericalField(name="new_field", description="My description", required=False, default=15.0,
                          value_type=float, value_range=(5.0, 512.0))
    assert field.validate(42.0) == 42.0

def test_validate_float_with_unbounded_range():
    """Test that any value is accepted when range has no bounds."""
    field = NumericalField(name="new_field", description="My description", required=False, default=1.0,
                          value_type=float, value_range=[None, None])
    assert field.validate(42.1) == 42.1

def test_validate_float_with_min_only_range():
    """Test that values above minimum are accepted when only min is specified in range."""
    field = NumericalField(name="new_field", description="My description", required=False, default=15.0,
                          value_type=float, value_range=[5, None])
    assert field.validate(42.2) == 42.2

def test_validate_float_with_max_only_range():
    """Test that values below maximum are accepted when only max is specified in range."""
    field = NumericalField(name="new_field", description="My description", required=False, default=1.0,
                          value_type=float, value_range=[None, 512.2])
    assert field.validate(42.2) == 42.2

def test_validate_float_with_insufficient_range_values():
    """Test that range with insufficient values raises ValidationError."""
    with pytest.raises(ValidationError, match="Range must have 2 values, 1 provided"):
        NumericalField(name="new_field", description="My description", required=False, default=1.0,
                     value_type=float, value_range=[None])

def test_validate_float_with_excess_range_values():
    """Test that range with too many values raises ValidationError."""
    with pytest.raises(ValidationError, match="Range must have 2 values, 3 provided"):
        NumericalField(name="new_field", description="My description", required=False, default=1.0,
                     value_type=float, value_range=[None, None, None])

def test_validate_float_below_min_range():
    """Test that values below range minimum raise ValidationError."""
    field = NumericalField(name="new_field", description="My description", required=False, default=15.0,
                          value_type=float, value_range=(5.0, 512.0))
    with pytest.raises(ValidationError, match="Value must be at least"):
        field.validate(1.0)

def test_validate_float_above_max_range():
    """Test that values above range maximum raise ValidationError."""
    field = NumericalField(name="new_field", description="My description", required=False, default=15.0,
                          value_type=float, value_range=(5.0, 512.0))
    with pytest.raises(ValidationError, match="Value must be at most"):
        field.validate(1024.0)

def test_validate_float_invalid_min_max_order():
    """Test that min_value greater than max_value raises ValidationError."""
    with pytest.raises(ValidationError, match="Minimal value greater than maximal value"):
        NumericalField(name="new_field", description="My description", required=False, default=1.0,
                     value_type=float, min_value=512.1, max_value=5.2)

def test_validate_float_consistent_bounds():
    """Test that consistent min_value, max_value, and value_range are accepted."""
    field = NumericalField(name="new_field", description="My description", required=False, default=15.0,
                          value_type=float, min_value=5.2, max_value=512.3, value_range=(5.2, 512.3))
    assert field.validate(42.0) == 42.0

def test_validate_float_invalid_min_and_range_combination():
    """Test that min_value and value_range together raise ValidationError."""
    with pytest.raises(ValidationError, match="using range and lower bound"):
        NumericalField(name="new_field", description="My description", required=False, default=1.0,
                     value_type=float, min_value=5.2, value_range=(5.1, 512.3))

def test_validate_float_invalid_max_and_range_combination():
    """Test that max_value and value_range together raise ValidationError."""
    with pytest.raises(ValidationError, match="using range and upper bound"):
        NumericalField(name="new_field", description="My description", required=False, default=1.0,
                     value_type=float, max_value=512.4, value_range=(5.5, 512.6))

def test_validate_float_min_not_matching_range():
    """Test that min_value must match range lower bound when both are provided."""
    with pytest.raises(ValidationError, match="Lower bound value is not matching"):
        NumericalField(name="new_field", description="My description", required=False, default=1.0,
                     value_type=float, min_value=1.1, max_value=512.2, value_range=(5.3, 512.4))

def test_validate_float_max_not_matching_range():
    """Test that max_value must match range upper bound when both are provided."""
    with pytest.raises(ValidationError, match="Upper bound value is not matching"):
        NumericalField(name="new_field", description="My description", required=False, default=1.0,
                     value_type=float, min_value=5.1, max_value=1024.2, value_range=(5.1, 512.3))

def test_validate_float_rejects_none():
    """Test that None is rejected for non-required float fields."""
    field = NumericalField(name="new_field", description="My description", required=False, default=1.0,
                          value_type=float)
    with pytest.raises(ValidationError, match="Must be of type float"):
        field.validate(None)

def test_validate_float_rejects_non_numeric_string():
    """Test that non-numeric strings are rejected for float fields."""
    field = NumericalField(name="new_field", description="My description", required=False, default=1.0,
                          value_type=float)
    with pytest.raises(ValidationError, match="Must be of type float"):
        field.validate("str")

def test_validate_float_rejects_none_default():
    """Test that None as default value raises FormatError."""
    with pytest.raises(FormatError, match="invalid default value"):
        NumericalField(value_type=float, name="new_field", description="My description",
                     required=False, default=None)

def test_validate_float_rejects_boolean_default():
    """Test that boolean as default value raises FormatError."""
    with pytest.raises(FormatError, match="invalid default value"):
        NumericalField(value_type=float, name="new_field", description="My description",
                     required=False, default=True)

def test_validate_float_rejects_string_default():
    """Test that empty string as default value raises FormatError."""
    with pytest.raises(FormatError, match="invalid default value"):
        NumericalField(value_type=float, name="new_field", description="My description",
                     required=False, default="")

def test_validate_float_rejects_default_below_min_value():
    """Test that default value below min_value raises FormatError."""
    with pytest.raises(FormatError, match="invalid default value"):
        NumericalField(name="new_field", description="My description", required=False, default=1.0,
                     value_type=float, min_value=5.0)

def test_validate_float_rejects_default_below_range():
    """Test that default value below value_range raises FormatError."""
    with pytest.raises(FormatError, match="invalid default value"):
        NumericalField(name="new_field", description="My description", required=False, default=1.0,
                     value_type=float, value_range=[5.0, 1024.0])

def test_validate_float_rejects_default_above_max_value():
    """Test that default value above max_value raises FormatError."""
    with pytest.raises(FormatError, match="invalid default value"):
        NumericalField(name="new_field", description="My description", required=False, default=1024.0,
                     value_type=float, max_value=512.0)

def test_validate_float_rejects_default_above_range():
    """Test that default value above value_range raises FormatError."""
    with pytest.raises(FormatError, match="invalid default value"):
        NumericalField(name="new_field", description="My description", required=False, default=2048.0,
                     value_type=float, value_range=[5.0, 1024.0])

def test_validate_string_converts_empty_string():
    """Test that StringField converts empty string correctly."""
    field = StringField(name="new_field", description="My description", required=False, default="",
                       min_length=0, max_length=-1, cast_to_string=True)
    assert field.validate("") == ""

def test_validate_string_converts_none_string():
    """Test that StringField converts 'None' string correctly."""
    field = StringField(name="new_field", description="My description", required=False, default="",
                       min_length=0, max_length=-1, cast_to_string=True)
    assert field.validate("None") == "None"

def test_validate_string_converts_none_to_empty_string():
    """Test that StringField converts None to empty string when not required."""
    field = StringField(name="new_field", description="My description", required=False, default="",
                       min_length=0, max_length=-1, cast_to_string=True)
    assert field.validate(None) == "None"

def test_validate_string_converts_number_string():
    """Test that StringField converts number string correctly."""
    field = StringField(name="new_field", description="My description", required=False, default="",
                       min_length=0, max_length=-1, cast_to_string=True)
    assert field.validate("123") == "123"

def test_validate_string_converts_integer():
    """Test that StringField converts integer to string."""
    field = StringField(name="new_field", description="My description", required=False, default="",
                       min_length=0, max_length=-1, cast_to_string=True)
    assert field.validate(123) == "123"

def test_validate_string_handles_none():
    """Test that StringField handles None values when not required."""
    field = StringField(name="new_field", description="My description", required=False, default="",
                       min_length=0, max_length=-1, cast_to_string=True)
    assert field.validate(None) == "None"

def test_validate_string_rejects_none_when_required():
    """Test that StringField rejects None when required is True."""
    field = StringField(name="new_field", description="My description", required=True, default="",
                       min_length=0, max_length=-1, cast_to_string=False)
    with pytest.raises(ValidationError, match="Cannot be None"):
        field.validate(None)

def test_validate_string_without_casting():
    """Test that StringField rejects non-string values when cast_to_string is False."""
    field = StringField(name="new_field", description="My description", required=False, default="",
                       min_length=0, max_length=-1, cast_to_string=False)
    # String input should work
    assert field.validate("test") == "test"
    # Non-string input should raise error
    with pytest.raises(ValidationError):
        field.validate(123)

def test_validate_string_rejects_invalid_default():
    """Test that invalid default values raise FormatError."""
    with pytest.raises(FormatError):
        StringField(name="new_field", description="My description", required=False, default=None,
                   min_length=0, max_length=-1, cast_to_string=False)

def test_validate_large_positive_int():
    """Test that very large positive integers are handled correctly."""
    large_int = sys.maxsize - 1
    field = NumericalField(name="large_int", description="Test large positive integer",
                         required=False, default=0, value_type=int)
    assert field.validate(large_int) == large_int


def test_validate_large_negative_int():
    """Test that very large negative integers are handled correctly."""
    small_int = -sys.maxsize + 1
    field = NumericalField(name="small_int", description="Test large negative integer",
                         required=False, default=0, value_type=int)
    assert field.validate(small_int) == small_int


def test_validate_int_string_representation():
    """Test that string representations of large integers are converted correctly."""
    large_int = sys.maxsize - 1
    small_int = -sys.maxsize + 1
    field = NumericalField(name="int_strings", description="Test int string conversion",
                         required=False, default=0, value_type=int)
    
    assert field.validate(str(large_int)) == large_int
    assert field.validate(str(small_int)) == small_int


def test_bounded_int_validation():
    """Test that bounded integer validation works with large values."""
    large_int = sys.maxsize - 1
    small_int = -sys.maxsize + 1
    
    bounded_field = NumericalField(name="bounded_int", description="Bounded large int",
                                  required=False, default=0, value_type=int,
                                  min_value=small_int, max_value=large_int)
    
    # Test valid bounds
    assert bounded_field.validate(large_int) == large_int
    assert bounded_field.validate(small_int) == small_int


def test_int_upper_boundary_violation():
    """Test that values above maximum bound raise ValidationError."""
    large_int = sys.maxsize - 1
    bounded_field = NumericalField(name="bounded_int", description="Test upper bound",
                                 required=False, default=0, value_type=int,
                                 max_value=large_int)
    
    with pytest.raises(ValidationError, match="Value must be at most"):
        bounded_field.validate(sys.maxsize + 1)


def test_int_lower_boundary_violation():
    """Test that values below minimum bound raise ValidationError."""
    small_int = -sys.maxsize + 1
    bounded_field = NumericalField(name="bounded_int", description="Test lower bound",
                                 required=False, default=0, value_type=int,
                                 min_value=small_int)
    
    with pytest.raises(ValidationError, match="Value must be at least"):
        bounded_field.validate(-sys.maxsize - 2)


def test_validate_positive_scientific_notation():
    """Test that positive scientific notation is properly parsed."""
    field = NumericalField(name="sci_float", description="Positive scientific notation",
                         required=False, default=0.0, value_type=float)
    
    assert field.validate("1.23e-4") == 0.000123
    assert field.validate("1.23e4") == 12300.0


def test_validate_negative_scientific_notation():
    """Test that negative numbers in scientific notation are properly parsed."""
    field = NumericalField(name="sci_float_neg", description="Negative scientific notation",
                         required=False, default=0.0, value_type=float)
    
    assert field.validate("-1.23e-4") == -0.000123


def test_validate_case_insensitive_scientific_notation():
    """Test that scientific notation is case-insensitive."""
    field = NumericalField(name="sci_float_case", description="Case-insensitive scientific notation",
                         required=False, default=0.0, value_type=float)
    
    assert field.validate("1.23E-4") == 0.000123
    assert field.validate("1.23E4") == 12300.0


def test_validate_simple_scientific_notation():
    """Test simple scientific notation without decimal places."""
    field = NumericalField(name="sci_float_simple", description="Simple scientific notation",
                         required=False, default=0.0, value_type=float)
    
    assert field.validate("1e6") == 1000000.0
    assert field.validate("1e-6") == 0.000001


def test_validate_float_limits_scientific_notation():
    """Test scientific notation near float limits."""
    field = NumericalField(name="sci_float_limits", description="Float limits in scientific notation",
                         required=False, default=0.0, value_type=float)
    
    # Near max float
    assert field.validate("1.7976931348623157e+308") == 1.7976931348623157e+308
    # Near min positive float
    assert field.validate("2.2250738585072014e-308") == 2.2250738585072014e-308


def test_validate_invalid_scientific_notation_missing_exponent():
    """Test that scientific notation with missing exponent raises ValidationError."""
    field = NumericalField(name="sci_float_invalid1", description="Invalid scientific notation - missing exponent",
                         required=False, default=0.0, value_type=float)
    
    with pytest.raises(ValidationError, match="Must be of type float"):
        field.validate("1.23e")


def test_validate_invalid_scientific_notation_missing_number():
    """Test that scientific notation with missing number raises ValidationError."""
    field = NumericalField(name="sci_float_invalid2", description="Invalid scientific notation - missing number",
                         required=False, default=0.0, value_type=float)
    
    with pytest.raises(ValidationError, match="Must be of type float"):
        field.validate("e123")


def test_validate_invalid_scientific_notation_multiple_decimals():
    """Test that scientific notation with multiple decimals raises ValidationError."""
    field = NumericalField(name="sci_float_invalid3", description="Invalid scientific notation - multiple decimals",
                         required=False, default=0.0, value_type=float)
    
    with pytest.raises(ValidationError, match="Must be of type float"):
        field.validate("1.2.3e4")


def test_validate_decimal_objects():
    """Test that Decimal objects are properly converted to float."""
    field = NumericalField(name="decimal_objects", description="Decimal to float conversion",
                         required=False, default=0.0, value_type=float)
    
    test_cases = [
        (Decimal("123.456"), 123.456),
        (Decimal("-123.456"), -123.456),
        (Decimal("1e-6"), 1e-6),
        (Decimal("1e6"), 1e6)
    ]
    
    for decimal_val, expected_float in test_cases:
        assert field.validate(decimal_val) == expected_float, f"Failed for {decimal_val}"


def test_validate_decimal_strings():
    """Test that Decimal-format strings are properly parsed and converted."""
    field = NumericalField(name="decimal_strings", description="Decimal string parsing",
                         required=False, default=0.0, value_type=float)
    
    test_cases = [
        ("123.456", 123.456),
        ("-123.456", -123.456),
        ("1e-6", 1e-6),
        ("1e6", 1e6)
    ]
    
    for decimal_str, expected_float in test_cases:
        assert field.validate(Decimal(decimal_str)) == expected_float, f"Failed for {decimal_str}"


def test_validate_fraction_objects():
    """Test that Fraction objects are properly converted to float."""
    field = NumericalField(name="fraction_objects", description="Fraction to float conversion",
                         required=False, default=0.0, value_type=float)
    
    test_cases = [
        (Fraction(1, 2), 0.5),
        (Fraction(3, 4), 0.75),
        (Fraction(-2, 3), -2/3),
        (Fraction(10, 2), 5.0)
    ]
    
    for fraction, expected_float in test_cases:
        assert abs(field.validate(fraction) - expected_float) < 1e-10, f"Failed for {fraction}"


def test_validate_fraction_strings():
    """Test that Fraction-format strings are properly parsed and converted."""
    field = NumericalField(name="fraction_strings", description="Fraction string parsing",
                         required=False, default=0.0, value_type=float)
    
    test_cases = [
        ("1/2", 0.5),
        ("3/4", 0.75),
        ("-2/3", -2/3),
        ("10/2", 5.0)
    ]
    
    for fraction_str, expected_float in test_cases:
        result = field.validate(Fraction(fraction_str))
        assert abs(result - expected_float) < 1e-10, f"Failed for {fraction_str}"


def test_validate_fraction_within_bounds():
    """Test that Fraction values within bounds are accepted."""
    bounded_field = NumericalField(name="bounded_fraction", 
                                 description="Bounded fraction validation",
                                 required=False,
                                 default=0.5,
                                 value_type=float, 
                                 min_value=0.1, 
                                 max_value=0.9)
    
    assert bounded_field.validate(Fraction(1, 2)) == 0.5


def test_validate_fraction_below_min_bound():
    """Test that Fraction values below minimum bound raise ValidationError."""
    bounded_field = NumericalField(name="min_bounded_fraction", 
                                 description="Minimum bound fraction validation",
                                 required=False,
                                 default=0.5,
                                 value_type=float, 
                                 min_value=0.1)
    
    with pytest.raises(ValidationError, match="Value must be at least"):
        bounded_field.validate(Fraction(1, 100))


def test_validate_fraction_above_max_bound():
    """Test that Fraction values above maximum bound raise ValidationError."""
    bounded_field = NumericalField(name="max_bounded_fraction", 
                                 description="Maximum bound fraction validation",
                                 required=False,
                                 default=0.5,
                                 value_type=float, 
                                 max_value=0.9)
    
    with pytest.raises(ValidationError, match="Value must be at most"):
        bounded_field.validate(Fraction(1, 1))


def test_validate_string_rejects_none_string_when_disabled():
    """Test that StringField rejects 'None' string when cast_to_string is False."""
    field = StringField(name="new_field", description="My description", required=False, default="some_value",
                      min_length=0, max_length=-1, cast_to_string=False)
    with pytest.raises(ValidationError, match="Expected string"):
        field.validate(None)

def test_validate_string_rejects_none_when_disabled():
    """Test that StringField rejects None when cast_to_string is False."""
    field = StringField(name="new_field", description="My description", required=False, default="some_value",
                      min_length=0, max_length=-1, cast_to_string=False)
    with pytest.raises(ValidationError, match="Expected string"):
        field.validate(None)

def test_validate_string_rejects_negative_min_length():
    """Test that StringField rejects negative min_length."""
    with pytest.raises(FormatError, match="smaller than 0"):
        StringField(name="new_field", description="My description", required=False, default="SomeString",
                   min_length=-1, max_length=-1, cast_to_string=True)

def test_validate_string_rejects_max_less_than_min():
    """Test that StringField rejects max_length less than min_length."""
    with pytest.raises(FormatError, match="smaller than min"):
        StringField(name="new_field", description="My description", required=False, default="SomeString",
                   min_length=10, max_length=0, cast_to_string=True)

def test_validate_string_rejects_default_shorter_than_min():
    """Test that StringField rejects default value shorter than min_length."""
    with pytest.raises(FormatError, match="invalid default value"):
        StringField(name="new_field", description="My description", required=False, default="SomeString",
                   min_length=15, max_length=100, cast_to_string=True)

def test_validate_string_rejects_value_shorter_than_min():
    """Test that StringField rejects value shorter than min_length."""
    field = StringField(name="new_field", description="My description", required=False, 
                       default="SomeLongLongString", min_length=15, max_length=100, 
                       cast_to_string=True)
    with pytest.raises(ValidationError, match="Value must be at least"):
        field.validate("SomeString")

def test_validate_string_rejects_value_longer_than_max():
    """Test that StringField rejects value longer than max_length."""
    field = StringField(name="new_field", description="My description", required=False, 
                       default="test", min_length=0, max_length=5, 
                       cast_to_string=True)
    with pytest.raises(ValidationError, match="Value must be at most"):
        field.validate("SomeString")

def test_validate_string_preserves_leading_trailing_whitespace():
    """Test that leading and trailing whitespace is preserved in string values."""
    field = StringField(name="new_field", description="Leading/trailing whitespace test", 
                       required=False, default="default", min_length=0, max_length=20, 
                       cast_to_string=False)
    assert field.validate("  test  ") == "  test  "


def test_validate_string_preserves_internal_whitespace():
    """Test that internal whitespace is preserved in string values."""
    field = StringField(name="new_field", description="Internal whitespace test", 
                       required=False, default="default", min_length=0, max_length=20, 
                       cast_to_string=False)
    assert field.validate("test string") == "test string"


def test_validate_string_handles_only_whitespace():
    """Test that strings containing only whitespace are handled correctly."""
    field = StringField(name="new_field", description="Whitespace-only test", 
                       required=False, default="default", min_length=0, max_length=20, 
                       cast_to_string=False)
    assert field.validate("   ") == "   "

def test_validate_string_unicode_characters():
    """Test that Unicode characters are handled correctly."""
    field = StringField(name="new_field", description="Handles Unicode", required=False,
                       default="default", min_length=0, max_length=-1, cast_to_string=False)
    
    # Test various Unicode characters
    test_strings = [
        "こんにちは",  # Japanese
        "Привет",     # Russian
        "مرحبا",      # Arabic
        "😊👍🌟"       # Emojis
    ]
    
    for s in test_strings:
        assert field.validate(s) == s

def test_validate_string_empty_string():
    """Test that an empty string is accepted when min_length is 0."""
    field = StringField(name="new_field", description="Empty string test", required=False,
                       default="", min_length=0, max_length=100, cast_to_string=True)
    assert field.validate("") == ""


def test_validate_string_long_string_rejected():
    """Test that a string longer than max_length raises ValidationError."""
    field = StringField(name="new_field", description="Long string test", required=False,
                       default="", min_length=0, max_length=100, cast_to_string=True)
    long_string = "x" * 1000
    with pytest.raises(ValidationError, match="at most 100 characters"):
        field.validate(long_string)


def test_validate_string_control_characters():
    """Test that strings with control characters are handled correctly."""
    field = StringField(name="new_field", description="Control chars test", required=False,
                       default="", min_length=0, max_length=100, cast_to_string=True)
    assert field.validate("line1\nline2\r\nline3") == "line1\nline2\r\nline3"

def test_validate_string_handles_none_strings():
    """Test that string 'None' variations are handled as regular strings."""
    field = StringField(name="new_field", description="None handling", required=False, 
                       default="default", min_length=0, max_length=100, cast_to_string=True)
    
    # These should all be treated as regular strings
    assert field.validate("None") == "None"
    assert field.validate("none") == "none"
    assert field.validate("NONE") == "NONE"


def test_validate_string_without_casting_handles_strings():
    """Test that string inputs work when cast_to_string is False."""
    field = StringField(name="new_field", description="String handling", required=False, 
                       default="", min_length=0, max_length=100, cast_to_string=False)
    
    # Regular strings should work fine
    assert field.validate("test") == "test"
    assert field.validate("None") == "None"  # Treated as regular string
    assert field.validate("123") == "123"    # Numbers as strings are fine
    
    # Non-string inputs should raise error
    with pytest.raises(ValidationError, match="Expected string"):
        field.validate(123)  # Integer
    with pytest.raises(ValidationError, match="Expected string"):
        field.validate(True)  # Boolean


def test_validate_string_rejects_none_when_required():
    """Test that None value is rejected when required is True."""
    field = StringField(name="new_field", description="None handling", required=True, 
                       default="default", min_length=0, max_length=100, cast_to_string=False)
    
    with pytest.raises(ValidationError):
        field.validate(None)

def test_validate_string_exact_min_length():
    """Test that a string with exact min_length is accepted."""
    field = StringField(name="new_field", description="Min length test", required=False,
                       default="123", min_length=3, max_length=5, cast_to_string=True)
    assert field.validate("123") == "123"


def test_validate_string_exact_max_length():
    """Test that a string with exact max_length is accepted."""
    field = StringField(name="new_field", description="Max length test", required=False,
                       default="123", min_length=3, max_length=5, cast_to_string=True)
    assert field.validate("12345") == "12345"


def test_validate_string_below_min_length():
    """Test that a string below min_length raises ValidationError."""
    field = StringField(name="new_field", description="Below min test", required=False,
                       default="123", min_length=3, max_length=5, cast_to_string=True)
    with pytest.raises(ValidationError, match="at least 3 characters"):
        field.validate("12")


def test_validate_string_above_max_length():
    """Test that a string above max_length raises ValidationError."""
    field = StringField(name="new_field", description="Above max test", required=False,
                       default="123", min_length=3, max_length=5, cast_to_string=True)
    with pytest.raises(ValidationError, match="at most 5 characters"):
        field.validate("123456")

def test_validate_string_special_characters():
    """Test that special characters are handled correctly."""
    field = StringField(name="new_field", description="Special chars", required=False,
                       default="default", min_length=0, max_length=100, cast_to_string=True)
    
    special_strings = [
        "!@#$%^&*()_+-=[]{}|;':\",./<>?",  # Special chars
        "\t\n\r\f\v",                      # Whitespace chars
        "\x00\x01\x02\x03\x04\x05",        # Control chars
        "'\""                               # Quotes
    ]
    
    for s in special_strings:
        assert field.validate(s) == s
