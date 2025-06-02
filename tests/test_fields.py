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

# testing float
def test_valid_float():
    field = NumericalField(name="new_field", description="My description",  required=False, default=1,
                           value_type=float, min_value=None, max_value=None, value_range=None)
    assert field.name == "new_field" and field.description == "My description" and not field.required

    confirmed_value = field.validate(123.0)
    assert confirmed_value == 123.0

    confirmed_value = field.validate("123.5")
    assert confirmed_value == 123.5

    confirmed_value = field.validate(0.0)
    assert confirmed_value == 0.0

    confirmed_value = field.validate(0)
    assert confirmed_value == 0.0

    confirmed_value = field.validate(-1093257.2)
    assert confirmed_value == -1093257.2

def test_valid_float_min_value():
    field = NumericalField(name="new_field", description="My description",  required=False, default=15.0,
                           value_type=float, min_value=10.0, max_value=None, value_range=None)
    assert field.name == "new_field" and field.description == "My description" and not field.required

    confirmed_value = field.validate(42.0)
    assert confirmed_value == 42.0

    confirmed_value = field.validate(10.01)
    assert confirmed_value == 10.01

def test_invalid_float_min_value():
    field = NumericalField(name="new_field", description="My description",  required=False, default=15.0,
                           value_type=float, min_value=10.0, max_value=None, value_range=None)
    assert field.name == "new_field" and field.description == "My description" and not field.required

    with pytest.raises(ValidationError, match="Value must be at least"):
        field.validate(2.2)

def test_valid_float_max_value():
    field = NumericalField(name="new_field", description="My description",  required=False, default=1,
                           value_type=float, min_value=None, max_value=512, value_range=None)
    assert field.name == "new_field" and field.description == "My description" and not field.required

    confirmed_value = field.validate(42.1)
    assert confirmed_value == 42.1

def test_invalid_float_max_value():
    field = NumericalField(name="new_field", description="My description",  required=False, default=1,
                           value_type=float, min_value=None, max_value=512, value_range=None)
    assert field.name == "new_field" and field.description == "My description" and not field.required

    with pytest.raises(ValidationError, match="Value must be at most"):
        field.validate(1024.5)

def test_valid_float_ranges_value_array():
    field = NumericalField(name="new_field", description="My description",  required=False, default=15.0,
                           value_type=float, min_value=None, max_value=None, value_range=[5.0, 512.0])
    assert field.name == "new_field" and field.description == "My description" and not field.required

    confirmed_value = field.validate(42.0)
    assert confirmed_value == 42.0

def test_valid_float_ranges_value_tuple():
    field = NumericalField(name="new_field", description="My description",  required=False, default=15.0,
                           value_type=float, min_value=None, max_value=None, value_range=(5.0, 512.0))
    assert field.name == "new_field" and field.description == "My description" and not field.required

    confirmed_value = field.validate(42.0)
    assert confirmed_value == 42.0

def test_valid_float_none_in_range():
    field = NumericalField(name="new_field", description="My description",  required=False, default=1,
                           value_type=float, min_value=None, max_value=None, value_range=[None, None])
    assert field.name == "new_field" and field.description == "My description" and not field.required

    confirmed_value = field.validate(42.1)
    assert confirmed_value == 42.1

def test_valid_float_min_and_none_in_range():
    field = NumericalField(name="new_field", description="My description",  required=False, default=15.0,
                           value_type=float, min_value=None, max_value=None, value_range=[5, None])
    assert field.name == "new_field" and field.description == "My description" and not field.required

    confirmed_value = field.validate(42.2)
    assert confirmed_value == 42.2

def test_valid_float_none_and_max_in_range():
    field = NumericalField(name="new_field", description="My description",  required=False, default=1,
                           value_type=float, min_value=None, max_value=None, value_range=[None, 512.2])
    assert field.name == "new_field" and field.description == "My description" and not field.required

    confirmed_value = field.validate(42.2)
    assert confirmed_value == 42.2

def test_invalid_float_range_not_enough_values():
    with pytest.raises(ValidationError, match="Range must have 2 values, 1 provided."):
        NumericalField(name="new_field", description="My description",  required=False, default=1,
                       value_type=float, min_value=None, max_value=None, value_range=[None])

def test_invalid_float_range_too_many_values():
    with pytest.raises(ValidationError, match="Range must have 2 values, 3 provided."):
        NumericalField(name="new_field", description="My description", required=False, default=1,
                       value_type=float, min_value=None, max_value=None, value_range=[None, None, None])

def test_invalid_float_out_of_range():
    field = NumericalField(name="new_field", description="My description",  required=False, default=15.0,
                           value_type=float, min_value=None, max_value=None, value_range=(5.0, 512.0))
    assert field.name == "new_field" and field.description == "My description" and not field.required

    with pytest.raises(ValidationError, match="Value must be at least"):
        field.validate(1.0)

    with pytest.raises(ValidationError, match="Value must be at most"):
        field.validate(1024.0)

def test_invalid_float_min_greater_than_max():
    with pytest.raises(ValidationError, match="Minimal value greater than maximal value"):
        NumericalField(name="new_field", description="My description",  required=False, default=1,
                        value_type=float, min_value=512.1, max_value=5.2, value_range=None)

def test_valid_float_min_max_and_range():
    NumericalField(name="new_field", description="My description",  required=False, default=15.0,
                   value_type=float, min_value=5.2, max_value=512.3, value_range=(5.2,512.3))

def test_invalid_float_min_and_range():
    with pytest.raises(ValidationError, match="using range and lower bound"):
        NumericalField(name="new_field", description="My description",  required=False, default=1,
                        value_type=float, min_value=5.2, max_value=None, value_range=(5.1,512.3))

def test_invalid_float_max_and_range():
    with pytest.raises(ValidationError, match="using range and upper bound"):
        NumericalField(name="new_field", description="My description",  required=False, default=1,
                        value_type=float, min_value=None, max_value=512.4, value_range=(5.5,512.6))

def test_invalid_float_min_not_match_range():
    with pytest.raises(ValidationError, match="Lower bound value is not matching"):
        NumericalField(name="new_field", description="My description",  required=False, default=1,
                        value_type=float, min_value=1.1, max_value=512.2, value_range=(5.3,512.4))

def test_invalid_float_max_not_match_range():
    with pytest.raises(ValidationError, match="Upper bound value is not matching"):
        NumericalField(name="new_field", description="My description",  required=False, default=1,
                        value_type=float, min_value=5.1, max_value=1024.2, value_range=(5.1,512.3))

def test_invalid_float_empty():
    field = NumericalField(name="new_field", description="My description", required=False, default=1,
                           value_type=float, min_value=None, max_value=None, value_range=None)
    assert field.name == "new_field" and field.description == "My description" and not field.required

    with pytest.raises(ValidationError, match="Must be of type float"):
        field.validate(None)

def test_invalid_float_string():
    field = NumericalField(name="new_field", description="My description", required=False, default=1,
                           value_type=float, min_value=None, max_value=None, value_range=None)
    assert field.name == "new_field" and field.description == "My description" and not field.required

    with pytest.raises(ValidationError, match="Must be of type float"):
        field.validate("str")

def test_invalid_float_invalid_default():
    with pytest.raises(FormatError, match="invalid default value"):
        NumericalField(value_type=float, name="new_field", description="My description", required=False, default=None)

    with pytest.raises(FormatError, match="invalid default value"):
        NumericalField(value_type=float, name="new_field", description="My description", required=False, default=True)

    with pytest.raises(FormatError, match="invalid default value"):
        NumericalField(value_type=float, name="new_field", description="My description", required=False, default="")

def test_invalid_float_default_under_min():
    with pytest.raises(FormatError, match="invalid default value"):
        NumericalField(name="new_field", description="My description", required=False, default=1,
                       value_type=float, min_value=5, max_value=None, value_range=None)

    with pytest.raises(FormatError, match="invalid default value"):
        NumericalField(name="new_field", description="My description", required=False, default=1,
                       value_type=float, min_value=None, max_value=None, value_range=[5, 1024])

def test_invalid_float_default_over_min():
    with pytest.raises(FormatError, match="invalid default value"):
        NumericalField(name="new_field", description="My description", required=False, default=1024,
                       value_type=float, min_value=None, max_value=512, value_range=None)

    with pytest.raises(FormatError, match="invalid default value"):
        NumericalField(name="new_field", description="My description", required=False, default=2048,
                       value_type=float, min_value=None, max_value=None, value_range=[5, 1024])

# testing String
def test_valid_string():
    field = StringField(name="new_field", description="My description", required=False, default=None,
                        min_length=0, max_length=-1, allow_string_to_be_none=True)
    assert field.name == "new_field" and field.description == "My description" and not field.required

    confirmed_value = field.validate("")
    assert confirmed_value == ""

    confirmed_value = field.validate("None")
    assert confirmed_value == "None"

    confirmed_value = field.validate(None)
    assert confirmed_value == "None"

    confirmed_value = field.validate("123")
    assert confirmed_value == "123"

    confirmed_value = field.validate(123)
    assert confirmed_value == "123"

def test_valid_none_string():
    field = StringField(name="new_field", description="My description", required=False, default=None,
                        min_length=0, max_length=-1, allow_string_to_be_none=True)
    assert field.name == "new_field" and field.description == "My description" and not field.required

    confirmed_value = field.validate("")
    assert confirmed_value == ""

    confirmed_value = field.validate("None")
    assert confirmed_value == "None"

    confirmed_value = field.validate(None)
    assert confirmed_value == "None"

    confirmed_value = field.validate("123")
    assert confirmed_value == "123"

    confirmed_value = field.validate(123)
    assert confirmed_value == "123"

def test_invalid_default_string():
    with pytest.raises(FormatError, match="invalid default value"):
        StringField(name="new_field", description="My description", required=False, default=None,
                    min_length=0, max_length=-1, allow_string_to_be_none=False)

    with pytest.raises(FormatError, match="invalid default value"):
        StringField(name="new_field", description="My description", required=False, default=None,
                    min_length=0, max_length=-1, allow_string_to_be_none=False)

def test_invalid_string():
    field = StringField(name="new_field", description="My description", required=False, default="some_value",
                    min_length=0, max_length=-1, allow_string_to_be_none=False)

    with pytest.raises(ValidationError, match="Must be of type string"):
        field.validate("None")

    with pytest.raises(ValidationError, match="Must be of type string"):
        field.validate(None)

def test_invalid_default_string():
    with pytest.raises(FormatError, match="smaller than 0"):
        StringField(name="new_field", description="My description", required=False, default="SomeString",
                    min_length=-1, max_length=-1, allow_string_to_be_none=True)

def test_invalid_string_min_greater_max():
    with pytest.raises(FormatError, match="smaller than min"):
        StringField(name="new_field", description="My description", required=False, default="SomeString",
                    min_length=10, max_length=0, allow_string_to_be_none=True)

def test_invalid_string_default_smaller_than_min():
    with pytest.raises(FormatError, match="invalid default value"):
        StringField(name="new_field", description="My description", required=False, default="SomeString",
                    min_length=15, max_length=100, allow_string_to_be_none=True)

def test_invalid_string_smaller_than_min():
    field = StringField(name="new_field", description="My description", required=False, default="SomeLongLongString",
                        min_length=15, max_length=100, allow_string_to_be_none=True)

    with pytest.raises(ValidationError, match="Value must be at least"):
        field.validate("SomeString")

def test_invalid_string_bigger_than_max():
    field = StringField(name="new_field", description="My description", required=False, default="test",
                        min_length=0, max_length=5, allow_string_to_be_none=True)

    with pytest.raises(ValidationError, match="Value must be at most"):
        field.validate("SomeString")
