import pytest

from readtheyaml.exceptions.format_error import FormatError
from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.fields.none_field import NoneField
from readtheyaml.fields.numerical_field import NumericalField


# testing None
def test_valid_none():
    field = NoneField(name="new_field", description="My description", required=True, default=None)
    assert field.name == "new_field" and field.description == "My description" and field.required

    confirmed_value = field.validate("None")
    assert confirmed_value is None

    confirmed_value = field.validate("none")
    assert confirmed_value is None

    confirmed_value = field.validate(None)
    assert confirmed_value is None

def test_invalid_none_empty():
    field = NoneField(name="new_field", description="My description", required=True, default=None)
    assert field.name == "new_field" and field.description == "My description" and field.required

    with pytest.raises(ValidationError, match="must be null/None"):
        field.validate("")

def test_invalid_none_numerical():
    field = NoneField(name="new_field", description="My description", required=True, default=None)
    assert field.name == "new_field" and field.description == "My description" and field.required

    with pytest.raises(ValidationError, match="must be null/None"):
        field.validate("123")

    with pytest.raises(ValidationError, match="must be null/None"):
        field.validate(123)

# testing int
def test_valid_int():
    field = NumericalField(name="new_field", description="My description",  required=True, default=1, 
                           value_type=int, min_value=None, max_value=None, value_range=None)
    assert field.name == "new_field" and field.description == "My description" and field.required

    confirmed_value = field.validate(123)
    assert confirmed_value == 123

    confirmed_value = field.validate("123")
    assert confirmed_value == 123

    confirmed_value = field.validate(0)
    assert confirmed_value == 0

    confirmed_value = field.validate(-1093257)
    assert confirmed_value == -1093257


def test_valid_int_min_value():
    field = NumericalField(name="new_field", description="My description",  required=True, default=1,
                           value_type=int, min_value=10, max_value=None, value_range=None)
    assert field.name == "new_field" and field.description == "My description" and field.required

    confirmed_value = field.validate(42)
    assert confirmed_value == 42

def test_invalid_int_min_value():
    field = NumericalField(name="new_field", description="My description",  required=True, default=1,
                           value_type=int, min_value=10, max_value=None, value_range=None)
    assert field.name == "new_field" and field.description == "My description" and field.required

    with pytest.raises(ValidationError, match="Value must be at least"):
        field.validate(2)

def test_valid_int_max_value():
    field = NumericalField(name="new_field", description="My description",  required=True, default=1,
                           value_type=int, min_value=None, max_value=512, value_range=None)
    assert field.name == "new_field" and field.description == "My description" and field.required

    confirmed_value = field.validate(42)
    assert confirmed_value == 42

def test_invalid_int_max_value():
    field = NumericalField(name="new_field", description="My description",  required=True, default=1,
                           value_type=int, min_value=None, max_value=512, value_range=None)
    assert field.name == "new_field" and field.description == "My description" and field.required

    with pytest.raises(ValidationError, match="Value must be at most"):
        field.validate(1024)

def test_valid_int_ranges_value_array():
    field = NumericalField(name="new_field", description="My description",  required=True, default=1,
                           value_type=int, min_value=None, max_value=None, value_range=[5, 512])
    assert field.name == "new_field" and field.description == "My description" and field.required

    confirmed_value = field.validate(42)
    assert confirmed_value == 42

def test_valid_int_ranges_value_tuple():
    field = NumericalField(name="new_field", description="My description",  required=True, default=1,
                           value_type=int, min_value=None, max_value=None, value_range=(5, 512))
    assert field.name == "new_field" and field.description == "My description" and field.required

    confirmed_value = field.validate(42)
    assert confirmed_value == 42

def test_valid_int_none_in_range():
    field = NumericalField(name="new_field", description="My description",  required=True, default=1,
                           value_type=int, min_value=None, max_value=None, value_range=[None, None])
    assert field.name == "new_field" and field.description == "My description" and field.required

    confirmed_value = field.validate(42)
    assert confirmed_value == 42

def test_valid_int_min_and_none_in_range():
    field = NumericalField(name="new_field", description="My description",  required=True, default=1,
                           value_type=int, min_value=None, max_value=None, value_range=[5, None])
    assert field.name == "new_field" and field.description == "My description" and field.required

    confirmed_value = field.validate(42)
    assert confirmed_value == 42

def test_valid_int_none_and_max_in_range():
    field = NumericalField(name="new_field", description="My description",  required=True, default=1,
                           value_type=int, min_value=None, max_value=None, value_range=[None, 512])
    assert field.name == "new_field" and field.description == "My description" and field.required

    confirmed_value = field.validate(42)
    assert confirmed_value == 42

def test_invalid_int_range_not_enough_values():
    with pytest.raises(ValidationError, match="Range must have 2 values, 1 provided."):
        NumericalField(name="new_field", description="My description",  required=True, default=1,
                       value_type=int, min_value=None, max_value=None, value_range=[None])


def test_invalid_int_range_too_many_values():
    with pytest.raises(ValidationError, match="Range must have 2 values, 3 provided."):
        NumericalField(name="new_field", description="My description", required=True, default=1,
                       value_type=int, min_value=None, max_value=None, value_range=[None, None, None])

def test_invalid_int_out_of_range():
    field = NumericalField(name="new_field", description="My description",  required=True, default=1,
                           value_type=int, min_value=None, max_value=None, value_range=(5, 512))
    assert field.name == "new_field" and field.description == "My description" and field.required

    with pytest.raises(ValidationError, match="Value must be at least"):
        field.validate(1)

    with pytest.raises(ValidationError, match="Value must be at most"):
        field.validate(1024)

def test_invalid_int_min_greater_than_max():
    with pytest.raises(ValidationError, match="Minimal value greater than maximal value"):
        NumericalField(name="new_field", description="My description",  required=True, default=1,
                        value_type=int, min_value=512, max_value=5, value_range=None)

def test_invalid_int_min_and_range():
    with pytest.raises(ValidationError, match="using range and lower bound"):
        NumericalField(name="new_field", description="My description",  required=True, default=1,
                        value_type=int, min_value=5, max_value=None, value_range=(5,512))

def test_invalid_int_max_and_range():
    with pytest.raises(ValidationError, match="using range and upper bound"):
        NumericalField(name="new_field", description="My description",  required=True, default=1,
                        value_type=int, min_value=None, max_value=512, value_range=(5,512))

def test_invalid_int_min_not_match_range():
    with pytest.raises(ValidationError, match="Lower bound value is not matching"):
        NumericalField(name="new_field", description="My description",  required=True, default=1,
                        value_type=int, min_value=1, max_value=512, value_range=(5,512))

def test_invalid_int_max_not_match_range():
    with pytest.raises(ValidationError, match="Upper bound value is not matching"):
        NumericalField(name="new_field", description="My description",  required=True, default=1,
                        value_type=int, min_value=5, max_value=1024, value_range=(5,512))

def test_invalid_int_empty():
    field = NumericalField(name="new_field", description="My description", required=True, default=1,
                           value_type=int, min_value=None, max_value=None, value_range=None)
    assert field.name == "new_field" and field.description == "My description" and field.required

    with pytest.raises(ValidationError, match="Must be of type int"):
        field.validate(None)

def test_invalid_int_string():
    field = NumericalField(name="new_field", description="My description", required=True, default=1,
                           value_type=int, min_value=None, max_value=None, value_range=None)
    assert field.name == "new_field" and field.description == "My description" and field.required

    with pytest.raises(ValidationError, match="Must be of type int"):
        field.validate("str")