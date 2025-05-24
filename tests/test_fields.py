import pytest

from readtheyaml.exceptions.format_error import FormatError
from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.fields.bool_field import BoolField
from readtheyaml.fields.none_field import NoneField
from readtheyaml.fields.numerical_field import NumericalField


# testing None
def test_valid_none():
    field = NoneField(name="new_field", description="My description", required=False, default=None)
    assert field.name == "new_field" and field.description == "My description" and not field.required

    confirmed_value = field.validate("None")
    assert confirmed_value is None

    confirmed_value = field.validate("none")
    assert confirmed_value is None

    confirmed_value = field.validate(None)
    assert confirmed_value is None

def test_invalid_none_empty():
    field = NoneField(name="new_field", description="My description", required=False, default=None)
    assert field.name == "new_field" and field.description == "My description" and not field.required

    with pytest.raises(ValidationError, match="must be null/None"):
        field.validate("")

def test_invalid_none_numerical():
    field = NoneField(name="new_field", description="My description", required=False, default=None)
    assert field.name == "new_field" and field.description == "My description" and not field.required

    with pytest.raises(ValidationError, match="must be null/None"):
        field.validate("123")

    with pytest.raises(ValidationError, match="must be null/None"):
        field.validate(123)

def test_valid_none_text_default():
    field = NoneField(name="new_field", description="My description", required=False, default="None")
    assert field.name == "new_field" and field.description == "My description" and not field.required

def test_invalid_none_invalid_default():
    with pytest.raises(FormatError, match="invalid default value"):
        NoneField(name="new_field", description="My description", required=False, default=True)

    with pytest.raises(FormatError, match="invalid default value"):
        NoneField(name="new_field", description="My description", required=False, default=0)

    with pytest.raises(FormatError, match="invalid default value"):
        NoneField(name="new_field", description="My description", required=False, default="test")

# testing Bool
def test_valid_bool():
    field = BoolField(name="new_field", description="My description", required=False, default=True)
    assert field.name == "new_field" and field.description == "My description" and not field.required

    confirmed_value = field.validate(True)
    assert confirmed_value is True

    confirmed_value = field.validate("True")
    assert confirmed_value is True

    confirmed_value = field.validate(False)
    assert confirmed_value is False

    confirmed_value = field.validate("False")
    assert confirmed_value is False

def test_invalid_bool_empty():
    field = BoolField(name="new_field", description="My description", required=False, default=True)
    assert field.name == "new_field" and field.description == "My description" and not field.required

    with pytest.raises(ValidationError, match="Must be of type bool"):
        field.validate("")

def test_invalid_bool_numerical():
    field = BoolField(name="new_field", description="My description", required=False, default=True)
    assert field.name == "new_field" and field.description == "My description" and not field.required

    with pytest.raises(ValidationError, match="Expected a boolean value"):
        field.validate("123")

    with pytest.raises(ValidationError, match="Expected a boolean value"):
        field.validate(123)

def test_valid_bool_text_default():
    field = BoolField(name="new_field", description="My description", required=False, default="True")
    assert field.name == "new_field" and field.description == "My description" and not field.required

    field = BoolField(name="new_field", description="My description", required=False, default="False")
    assert field.name == "new_field" and field.description == "My description" and not field.required

def test_invalid_bool_invalid_default():
    with pytest.raises(FormatError, match="invalid default value"):
        BoolField(name="new_field", description="My description", required=False, default=None)

    with pytest.raises(FormatError, match="invalid default value"):
        BoolField(name="new_field", description="My description", required=False, default=0)

    with pytest.raises(FormatError, match="invalid default value"):
        BoolField(name="new_field", description="My description", required=False, default=12.5)

    with pytest.raises(FormatError, match="invalid default value"):
        BoolField(name="new_field", description="My description", required=False, default="")

# testing int
def test_valid_int():
    field = NumericalField(name="new_field", description="My description",  required=False, default=1, 
                           value_type=int, min_value=None, max_value=None, value_range=None)
    assert field.name == "new_field" and field.description == "My description" and not field.required

    confirmed_value = field.validate(123)
    assert confirmed_value == 123

    confirmed_value = field.validate("123")
    assert confirmed_value == 123

    confirmed_value = field.validate(0)
    assert confirmed_value == 0

    confirmed_value = field.validate(-1093257)
    assert confirmed_value == -1093257

def test_valid_int_min_value():
    field = NumericalField(name="new_field", description="My description",  required=False, default=15,
                           value_type=int, min_value=10, max_value=None, value_range=None)
    assert field.name == "new_field" and field.description == "My description" and not field.required

    confirmed_value = field.validate(42)
    assert confirmed_value == 42

def test_invalid_int_min_value():
    field = NumericalField(name="new_field", description="My description",  required=False, default=15,
                           value_type=int, min_value=10, max_value=None, value_range=None)
    assert field.name == "new_field" and field.description == "My description" and not field.required

    with pytest.raises(ValidationError, match="Value must be at least"):
        field.validate(2)

def test_valid_int_max_value():
    field = NumericalField(name="new_field", description="My description",  required=False, default=1,
                           value_type=int, min_value=None, max_value=512, value_range=None)
    assert field.name == "new_field" and field.description == "My description" and not field.required

    confirmed_value = field.validate(42)
    assert confirmed_value == 42

def test_invalid_int_max_value():
    field = NumericalField(name="new_field", description="My description",  required=False, default=1,
                           value_type=int, min_value=None, max_value=512, value_range=None)
    assert field.name == "new_field" and field.description == "My description" and not field.required

    with pytest.raises(ValidationError, match="Value must be at most"):
        field.validate(1024)

def test_valid_int_ranges_value_array():
    field = NumericalField(name="new_field", description="My description",  required=False, default=15,
                           value_type=int, min_value=None, max_value=None, value_range=[5, 512])
    assert field.name == "new_field" and field.description == "My description" and not field.required

    confirmed_value = field.validate(42)
    assert confirmed_value == 42

def test_valid_int_ranges_value_tuple():
    field = NumericalField(name="new_field", description="My description",  required=False, default=15,
                           value_type=int, min_value=None, max_value=None, value_range=(5, 512))
    assert field.name == "new_field" and field.description == "My description" and not field.required

    confirmed_value = field.validate(42)
    assert confirmed_value == 42

def test_valid_int_none_in_range():
    field = NumericalField(name="new_field", description="My description",  required=False, default=1,
                           value_type=int, min_value=None, max_value=None, value_range=[None, None])
    assert field.name == "new_field" and field.description == "My description" and not field.required

    confirmed_value = field.validate(42)
    assert confirmed_value == 42

def test_valid_int_min_and_none_in_range():
    field = NumericalField(name="new_field", description="My description",  required=False, default=15,
                           value_type=int, min_value=None, max_value=None, value_range=[5, None])
    assert field.name == "new_field" and field.description == "My description" and not field.required

    confirmed_value = field.validate(42)
    assert confirmed_value == 42

def test_valid_int_none_and_max_in_range():
    field = NumericalField(name="new_field", description="My description",  required=False, default=1,
                           value_type=int, min_value=None, max_value=None, value_range=[None, 512])
    assert field.name == "new_field" and field.description == "My description" and not field.required

    confirmed_value = field.validate(42)
    assert confirmed_value == 42

def test_invalid_int_range_not_enough_values():
    with pytest.raises(ValidationError, match="Range must have 2 values, 1 provided."):
        NumericalField(name="new_field", description="My description",  required=False, default=1,
                       value_type=int, min_value=None, max_value=None, value_range=[None])


def test_invalid_int_range_too_many_values():
    with pytest.raises(ValidationError, match="Range must have 2 values, 3 provided."):
        NumericalField(name="new_field", description="My description", required=False, default=1,
                       value_type=int, min_value=None, max_value=None, value_range=[None, None, None])

def test_invalid_int_out_of_range():
    field = NumericalField(name="new_field", description="My description",  required=False, default=15,
                           value_type=int, min_value=None, max_value=None, value_range=(5, 512))
    assert field.name == "new_field" and field.description == "My description" and not field.required

    with pytest.raises(ValidationError, match="Value must be at least"):
        field.validate(1)

    with pytest.raises(ValidationError, match="Value must be at most"):
        field.validate(1024)

def test_invalid_int_min_greater_than_max():
    with pytest.raises(ValidationError, match="Minimal value greater than maximal value"):
        NumericalField(name="new_field", description="My description",  required=False, default=1,
                        value_type=int, min_value=512, max_value=5, value_range=None)

def test_invalid_int_float_lower_bound():
    with pytest.raises(ValidationError, match="is not of type of the field"):
        NumericalField(name="new_field", description="My description",  required=False, default=1,
                        value_type=int, min_value=5.2, max_value=None, value_range=None)

def test_invalid_int_float_upper_bound():
    with pytest.raises(ValidationError, match="is not of type of the field"):
        NumericalField(name="new_field", description="My description",  required=False, default=1,
                        value_type=int, min_value=None, max_value=512.5, value_range=None)

def test_valid_float_min_max_and_range():
    NumericalField(name="new_field", description="My description",  required=False, default=1,
                   value_type=int, min_value=5, max_value=512, value_range=(5,512))

def test_invalid_int_min_and_range():
    with pytest.raises(ValidationError, match="using range and lower bound"):
        NumericalField(name="new_field", description="My description",  required=False, default=1,
                        value_type=int, min_value=5, max_value=None, value_range=(5,512))

def test_invalid_int_max_and_range():
    with pytest.raises(ValidationError, match="using range and upper bound"):
        NumericalField(name="new_field", description="My description",  required=False, default=1,
                        value_type=int, min_value=None, max_value=512, value_range=(5,512))

def test_invalid_int_min_not_match_range():
    with pytest.raises(ValidationError, match="Lower bound value is not matching"):
        NumericalField(name="new_field", description="My description",  required=False, default=1,
                        value_type=int, min_value=1, max_value=512, value_range=(5,512))

def test_invalid_int_max_not_match_range():
    with pytest.raises(ValidationError, match="Upper bound value is not matching"):
        NumericalField(name="new_field", description="My description",  required=False, default=1,
                        value_type=int, min_value=5, max_value=1024, value_range=(5,512))

def test_invalid_int_empty():
    field = NumericalField(name="new_field", description="My description", required=False, default=1,
                           value_type=int, min_value=None, max_value=None, value_range=None)
    assert field.name == "new_field" and field.description == "My description" and not field.required

    with pytest.raises(ValidationError, match="Must be of type int"):
        field.validate(None)

def test_invalid_int_string():
    field = NumericalField(name="new_field", description="My description", required=False, default=1,
                           value_type=int, min_value=None, max_value=None, value_range=None)
    assert field.name == "new_field" and field.description == "My description" and not field.required

    with pytest.raises(ValidationError, match="Must be of type int"):
        field.validate("str")

def test_valid_int_text_default():
    field = NumericalField(name="new_field", description="My description", required=False, default="0")
    assert field.name == "new_field" and field.description == "My description" and not field.required

    field = NumericalField(name="new_field", description="My description", required=False, default="125")
    assert field.name == "new_field" and field.description == "My description" and not field.required

def test_invalid_int_invalid_default():
    with pytest.raises(FormatError, match="invalid default value"):
        NumericalField(name="new_field", description="My description", required=False, default=None)

    with pytest.raises(FormatError, match="invalid default value"):
        NumericalField(name="new_field", description="My description", required=False, default=True)

    with pytest.raises(FormatError, match="invalid default value"):
        NumericalField(name="new_field", description="My description", required=False, default=12.5)

    with pytest.raises(FormatError, match="invalid default value"):
        NumericalField(name="new_field", description="My description", required=False, default="")

def test_invalid_int_default_under_min():
    with pytest.raises(FormatError, match="invalid default value"):
        NumericalField(name="new_field", description="My description", required=False, default=1,
                       value_type=int, min_value=5, max_value=None, value_range=None)

    with pytest.raises(FormatError, match="invalid default value"):
        NumericalField(name="new_field", description="My description", required=False, default=1,
                       value_type=int, min_value=None, max_value=None, value_range=[5, 1024])

def test_invalid_int_default_over_min():
    with pytest.raises(FormatError, match="invalid default value"):
        NumericalField(name="new_field", description="My description", required=False, default=1024,
                       value_type=int, min_value=None, max_value=512, value_range=None)

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