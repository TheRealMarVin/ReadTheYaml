import pytest

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
    field = StringField(name="new_field", description="My description", required=False, default=None,
                       min_length=0, max_length=-1, allow_string_to_be_none=True)
    assert field.validate("") == ""

def test_validate_string_converts_none_string():
    """Test that StringField converts 'None' string correctly."""
    field = StringField(name="new_field", description="My description", required=False, default=None,
                       min_length=0, max_length=-1, allow_string_to_be_none=True)
    assert field.validate("None") == "None"

def test_validate_string_converts_none_to_none_string():
    """Test that StringField converts None to 'None' string when allowed."""
    field = StringField(name="new_field", description="My description", required=False, default=None,
                       min_length=0, max_length=-1, allow_string_to_be_none=True)
    assert field.validate(None) == "None"

def test_validate_string_converts_number_string():
    """Test that StringField converts number string correctly."""
    field = StringField(name="new_field", description="My description", required=False, default=None,
                       min_length=0, max_length=-1, allow_string_to_be_none=True)
    assert field.validate("123") == "123"

def test_validate_string_converts_integer():
    """Test that StringField converts integer to string."""
    field = StringField(name="new_field", description="My description", required=False, default=None,
                       min_length=0, max_length=-1, allow_string_to_be_none=True)
    assert field.validate(123) == "123"

def test_validate_string_handles_none():
    """Test that StringField handles None values when allowed."""
    # Test with allow_string_to_be_none=True
    field = StringField(name="new_field", description="My description", required=False, default=None,
                       min_length=0, max_length=-1, allow_string_to_be_none=True)
    assert field.validate(None) == "None"

def test_validate_string_rejects_none_when_disabled():
    """Test that StringField rejects None when allow_string_to_be_none is False."""
    # Provide a valid default value that will pass validation
    field = StringField(name="new_field", description="My description", required=False, default="default",
                       min_length=0, max_length=-1, allow_string_to_be_none=False)
    with pytest.raises(ValidationError, match="Must be of type string"):
        field.validate(None)

def test_validate_string_rejects_invalid_default():
    """Test that invalid default values raise FormatError."""
    with pytest.raises(FormatError, match="invalid default value"):
        StringField(name="new_field", description="My description", required=False, default=None,
                   min_length=0, max_length=-1, allow_string_to_be_none=False)

def test_validate_string_rejects_none_string_when_disabled():
    """Test that StringField rejects 'None' string when allow_string_to_be_none is False."""
    field = StringField(name="new_field", description="My description", required=False, default="some_value",
                      min_length=0, max_length=-1, allow_string_to_be_none=False)
    with pytest.raises(ValidationError, match="Must be of type string"):
        field.validate("None")

def test_validate_string_rejects_none_when_disabled():
    """Test that StringField rejects None when allow_string_to_be_none is False."""
    field = StringField(name="new_field", description="My description", required=False, default="some_value",
                      min_length=0, max_length=-1, allow_string_to_be_none=False)
    with pytest.raises(ValidationError, match="Must be of type string"):
        field.validate(None)

def test_validate_string_rejects_negative_min_length():
    """Test that StringField rejects negative min_length."""
    with pytest.raises(FormatError, match="smaller than 0"):
        StringField(name="new_field", description="My description", required=False, default="SomeString",
                   min_length=-1, max_length=-1, allow_string_to_be_none=True)

def test_validate_string_rejects_max_less_than_min():
    """Test that StringField rejects max_length less than min_length."""
    with pytest.raises(FormatError, match="smaller than min"):
        StringField(name="new_field", description="My description", required=False, default="SomeString",
                   min_length=10, max_length=0, allow_string_to_be_none=True)

def test_validate_string_rejects_default_shorter_than_min():
    """Test that StringField rejects default value shorter than min_length."""
    with pytest.raises(FormatError, match="invalid default value"):
        StringField(name="new_field", description="My description", required=False, default="SomeString",
                   min_length=15, max_length=100, allow_string_to_be_none=True)

def test_validate_string_rejects_value_shorter_than_min():
    """Test that StringField rejects value shorter than min_length."""
    field = StringField(name="new_field", description="My description", required=False, 
                       default="SomeLongLongString", min_length=15, max_length=100, 
                       allow_string_to_be_none=True)
    with pytest.raises(ValidationError, match="Value must be at least"):
        field.validate("SomeString")

def test_validate_string_rejects_value_longer_than_max():
    """Test that StringField rejects value longer than max_length."""
    field = StringField(name="new_field", description="My description", required=False, 
                       default="test", min_length=0, max_length=5, 
                       allow_string_to_be_none=True)
    with pytest.raises(ValidationError, match="Value must be at most"):
        field.validate("SomeString")
