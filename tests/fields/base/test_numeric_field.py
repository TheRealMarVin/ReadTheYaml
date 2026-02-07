import pytest
from readtheyaml.fields.base.numerical_field import NumericalField
from readtheyaml.fields.field_factory import FIELD_FACTORY
from readtheyaml.exceptions.format_error import FormatError
from readtheyaml.exceptions.validation_error import ValidationError

# -----------------------------
# Field Creation
# -----------------------------

@pytest.mark.parametrize("type_str", ["int", "Int", "INT"])
def test_numerical_field_int_casing(type_str):
    """Factory should accept valid casing for int."""
    field = FIELD_FACTORY.create_field(
        type_str=type_str,
        name="number",
        description="test"
    )
    assert isinstance(field, NumericalField)
    assert field.value_type is int

@pytest.mark.parametrize("type_str", ["float", "Float", "FLOAT"])
def test_numerical_field_float_casing(type_str):
    """Factory should accept valid casing for float."""
    field = FIELD_FACTORY.create_field(
        type_str=type_str,
        name="number",
        description="test"
    )
    assert isinstance(field, NumericalField)
    assert field.value_type is float

def test_numerical_field_invalid_casing():
    """Invalid casing should raise ValueError."""
    with pytest.raises(ValueError):
        FIELD_FACTORY.create_field(type_str="INtT", name="bad", description="bad")

# -----------------------------
# Format Errors on Boundaries
# -----------------------------

def test_numerical_field_min_value_type_mismatch():
    """min_value not matching value_type should raise FormatError."""
    with pytest.raises(ValidationError):
        NumericalField(name="num", description="test", value_type=int, min_value=1.5)

def test_numerical_field_max_value_type_mismatch():
    """max_value not matching value_type should raise FormatError."""
    with pytest.raises(ValidationError):
        NumericalField(name="num", description="test", value_type=int, max_value=3.7)

# -----------------------------
# Validation of Values
# -----------------------------

@pytest.mark.parametrize("field_type,value", [("int", 42), ("float", 3.14)])
def test_numerical_field_accepts_valid_values(field_type, value):
    """NumericalField should accept correct values for int and float."""
    field = FIELD_FACTORY.create_field(
        type_str=field_type,
        name="num",
        description="test"
    )
    assert field.validate_and_build(value) == value

@pytest.mark.parametrize("value", ["abc", None, [], {}])
def test_numerical_field_rejects_invalid_values(value):
    """Non-numeric values should raise ValidationError."""
    field = NumericalField(name="num", description="test", value_type=int)
    with pytest.raises(ValidationError):
        field.validate_and_build(value)

@pytest.mark.parametrize("value", [True, False, "true", "false"])
def test_numerical_field_rejects_bools(value):
    """Booleans and boolean-like strings should raise ValidationError."""
    field = NumericalField(name="num", description="test", value_type=int)
    with pytest.raises(ValidationError):
        field.validate_and_build(value)

# -----------------------------
# Int vs Float edge cases
# -----------------------------

@pytest.mark.parametrize("value", [1.0, 2.0])
def test_int_field_accepts_integer_floats(value):
    """Float with no decimal part should be accepted by int field."""
    field = NumericalField(name="num", description="test", value_type=int)
    assert field.validate_and_build(value) == int(value)

@pytest.mark.parametrize("value", [3.5, 7.1])
def test_int_field_rejects_fractional_floats(value):
    """Float with decimal part should be rejected by int field."""
    field = NumericalField(name="num", description="test", value_type=int)
    with pytest.raises(ValidationError):
        field.validate_and_build(value)

# -----------------------------
# Range boundaries
# -----------------------------

def test_numerical_field_enforces_min_and_max():
    """NumericalField should enforce range limits."""
    field = NumericalField(name="num", description="test", value_type=int, min_value=5, max_value=10)

    assert field.validate_and_build(7) == 7
    with pytest.raises(ValidationError):
        field.validate_and_build(4)
    with pytest.raises(ValidationError):
        field.validate_and_build(11)
