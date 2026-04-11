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
    field = FIELD_FACTORY.create_field(type_str=type_str, name="number", description="test")
    assert isinstance(field, NumericalField)
    assert field.value_type is int

@pytest.mark.parametrize("type_str", ["float", "Float", "FLOAT"])
def test_numerical_field_float_casing(type_str):
    """Factory should accept valid casing for float."""
    field = FIELD_FACTORY.create_field(type_str=type_str, name="number", description="test")
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
    field = FIELD_FACTORY.create_field(type_str=field_type, name="num", description="test")
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


# -----------------------------
# Extended int coverage
# -----------------------------

@pytest.mark.parametrize("value,expected", [("123", 123), (0, 0), (-1093257, -1093257)])
def test_int_field_coercion_and_signs(value, expected):
    field = NumericalField(name="num", description="test", required=False, default=1, value_type=int)
    assert field.validate_and_build(value) == expected


@pytest.mark.parametrize("value_range,value,expected", [([5, 512], 42, 42), ((5, 512), 42, 42), ([None, None], 42, 42), ([5, None], 42, 42), ([None, 512], 42, 42)])
def test_int_field_accepts_supported_ranges(value_range, value, expected):
    field = NumericalField(name="num", description="test", required=False, default=15, value_type=int, value_range=value_range)

    assert field.validate_and_build(value) == expected


@pytest.mark.parametrize("value_range,value,match", [((5, 512), 1, "Value must be at least"), ((5, 512), 1024, "Value must be at most")])
def test_int_field_rejects_outside_range(value_range, value, match):
    field = NumericalField(name="num", description="test", required=False, default=15, value_type=int, value_range=value_range)

    with pytest.raises(ValidationError, match=match):
        field.validate_and_build(value)


# -----------------------------
# Bounds/range construction validation
# -----------------------------

@pytest.mark.parametrize(
    "value_type,default,value_range,match",
    [
        (int, 1, [None], "Range must have 2 values, 1 provided"),
        (int, 1, [None, None, None], "Range must have 2 values, 3 provided"),
        (float, 1.0, [None], "Range must have 2 values, 1 provided"),
        (float, 1.0, [None, None, None], "Range must have 2 values, 3 provided")
    ]
)
def test_numerical_field_rejects_invalid_range_length(value_type, default, value_range, match):
    with pytest.raises(ValidationError, match=match):
        NumericalField(name="num", description="test", required=False, default=default, value_type=value_type, value_range=value_range)


def test_numerical_field_rejects_min_greater_than_max():
    with pytest.raises(ValidationError, match="Minimal value greater than maximal value"):
        NumericalField(name="num", description="test", required=False, default=1, value_type=int, min_value=512, max_value=5)


def test_numerical_field_accepts_consistent_min_max_and_range():
    field = NumericalField(name="num", description="test", required=False, default=10, value_type=int, min_value=5, max_value=512, value_range=(5, 512))
    assert field.validate_and_build(42) == 42


@pytest.mark.parametrize(
    "kwargs,match",
    [
        ({"min_value": 5, "value_range": (5, 512)}, "using range and lower bound"),
        ({"max_value": 512, "value_range": (5, 512)}, "using range and upper bound"),
        ({"min_value": 1, "max_value": 512, "value_range": (5, 512)}, "Lower bound value is not matching"),
        ({"min_value": 5, "max_value": 1024, "value_range": (5, 512)}, "Upper bound value is not matching"),
    ],
)
def test_numerical_field_rejects_inconsistent_bound_combinations(kwargs, match):
    with pytest.raises(ValidationError, match=match):
        NumericalField(name="num", description="test", required=False, default=1, value_type=int, **kwargs)


# -----------------------------
# Default validation (int)
# -----------------------------

def test_int_field_accepts_numeric_string_default_and_converts():
    field = NumericalField(name="num", description="test", required=False, default="0")
    assert field.default == 0
    assert field.validate_and_build(0) == 0


@pytest.mark.parametrize("default", [None, True, 12.5, ""])
def test_int_field_rejects_invalid_default_types(default):
    with pytest.raises(FormatError, match="invalid default value"):
        NumericalField(name="num", description="test", required=False, default=default)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"default": 1, "value_type": int, "min_value": 5},
        {"default": 1, "value_type": int, "value_range": [5, 1024]},
        {"default": 1024, "value_type": int, "max_value": 512},
        {"default": 2048, "value_type": int, "value_range": [5, 1024]}
    ]
)
def test_int_field_rejects_default_outside_bounds(kwargs):
    with pytest.raises(FormatError, match="invalid default value"):
        NumericalField(name="num", description="test", required=False, **kwargs)


# -----------------------------
# Extended float coverage
# -----------------------------

@pytest.mark.parametrize("value,expected", [("123.5", 123.5), (0.0, 0.0), (0, 0.0), (-1093257.2, -1093257.2)])
def test_float_field_coercion_and_signs(value, expected):
    field = NumericalField(name="num", description="test", required=False, default=1.0, value_type=float)
    assert field.validate_and_build(value) == expected


@pytest.mark.parametrize("min_value,value", [(10.0, 10.0), (10.0, 10.01)])
def test_float_field_accepts_values_at_or_above_min(min_value, value):
    field = NumericalField(name="num", description="test", required=False, default=10.0, value_type=float, min_value=min_value)
    assert field.validate_and_build(value) == value


def test_float_field_rejects_below_min():
    field = NumericalField(name="num", description="test", required=False, default=15.0, value_type=float, min_value=10.0)
    with pytest.raises(ValidationError, match="Value must be at least"):
        field.validate_and_build(2.2)


def test_float_field_enforces_max():
    field = NumericalField(name="num", description="test", required=False, default=1.0, value_type=float, max_value=512.0)
    assert field.validate_and_build(42.1) == 42.1
    with pytest.raises(ValidationError, match="Value must be at most"):
        field.validate_and_build(1024.5)


@pytest.mark.parametrize(
    "value_range,value,expected",
    [
        ([5.0, 512.0], 42.0, 42.0),
        ((5.0, 512.0), 42.0, 42.0),
        ([None, None], 42.1, 42.1),
        ([5, None], 42.2, 42.2),
        ([None, 512.2], 42.2, 42.2)
    ]
)
def test_float_field_accepts_supported_ranges(value_range, value, expected):
    field = NumericalField(name="num", description="test", required=False, default=15.0, value_type=float, value_range=value_range)

    assert field.validate_and_build(value) == expected


@pytest.mark.parametrize("value_range,value,match", [((5.0, 512.0), 1.0, "Value must be at least"), ((5.0, 512.0), 1024.0, "Value must be at most")])
def test_float_field_rejects_outside_range(value_range, value, match):
    field = NumericalField(name="num", description="test", required=False, default=15.0, value_type=float, value_range=value_range)

    with pytest.raises(ValidationError, match=match):
        field.validate_and_build(value)


def test_float_field_rejects_invalid_min_max_order():
    with pytest.raises(ValidationError, match="Minimal value greater than maximal value"):
        NumericalField(name="num", description="test", required=False, default=1.0, value_type=float, min_value=512.1, max_value=5.2)


def test_float_field_accepts_consistent_bounds():
    field = NumericalField(
        name="num", description="test", required=False, default=15.0, value_type=float, min_value=5.2, max_value=512.3, value_range=(5.2, 512.3))
    assert field.validate_and_build(42.0) == 42.0


@pytest.mark.parametrize(
    "kwargs,match",
    [
        ({"min_value": 5.2, "value_range": (5.1, 512.3)}, "using range and lower bound"),
        ({"max_value": 512.4, "value_range": (5.5, 512.6)}, "using range and upper bound"),
        ({"min_value": 1.1, "max_value": 512.2, "value_range": (5.3, 512.4)}, "Lower bound value is not matching"),
        ({"min_value": 5.1, "max_value": 1024.2, "value_range": (5.1, 512.3)}, "Upper bound value is not matching"),
    ]
)
def test_float_field_rejects_inconsistent_bound_combinations(kwargs, match):
    with pytest.raises(ValidationError, match=match):
        NumericalField(name="num", description="test", required=False, default=1.0, value_type=float, **kwargs)


@pytest.mark.parametrize("value", [None, "str"])
def test_float_field_rejects_none_and_non_numeric_strings(value):
    field = NumericalField(name="num", description="test", required=False, default=1.0, value_type=float)
    with pytest.raises(ValidationError, match="Must be of type float"):
        field.validate_and_build(value)


@pytest.mark.parametrize("default", [None, True, ""])
def test_float_field_rejects_invalid_default_types(default):
    with pytest.raises(FormatError, match="invalid default value"):
        NumericalField(name="num", description="test", required=False, default=default, value_type=float)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"default": 1.0, "value_type": float, "min_value": 5.0},
        {"default": 1.0, "value_type": float, "value_range": [5.0, 1024.0]},
        {"default": 1024.0, "value_type": float, "max_value": 512.0},
        {"default": 2048.0, "value_type": float, "value_range": [5.0, 1024.0]},
    ],
)
def test_float_field_rejects_default_outside_bounds(kwargs):
    with pytest.raises(FormatError, match="invalid default value"):
        NumericalField(name="num", description="test", required=False, **kwargs)
