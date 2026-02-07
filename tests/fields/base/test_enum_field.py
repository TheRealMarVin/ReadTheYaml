import pytest
from readtheyaml.fields.base.enum_field import EnumField
from readtheyaml.fields.field_factory import FIELD_FACTORY
from readtheyaml.exceptions.format_error import FormatError
from readtheyaml.exceptions.validation_error import ValidationError


@pytest.mark.parametrize("casing", ["enum", "Enum", "ENUM"])
def test_enum_type_valid_casing(casing):
    """Factory should accept 'enum', 'Enum', and 'ENUM'."""
    field = FIELD_FACTORY.create_field(
        type_str=casing,
        name="my_enum",
        description="test",
        values=["a", "b"],
        required=False,
        default="a"
    )
    assert isinstance(field, EnumField)

@pytest.mark.parametrize("invalid", ["enuM", "enumm", "enums"])
def test_enum_type_invalid_casing(invalid):
    """Factory should reject incorrectly cased enum types."""
    with pytest.raises(ValueError):
        FIELD_FACTORY.create_field(
            type_str=invalid,
            name="my_enum",
            description="test",
            values=["a", "b"],
            required=False
        )

def test_enum_valid_value():
    """EnumField should accept a value that is in the list."""
    field = EnumField(name="color", description="Color", values=["red", "green"])
    assert field.validate_and_build("green") == "green"

def test_enum_invalid_value():
    """EnumField should reject a value that is not in the list."""
    field = EnumField(name="color", description="Color", values=["red", "green"])
    with pytest.raises(ValidationError):
        field.validate_and_build("blue")


def test_enum_valid_default_value():
    """Factory should accept valid default value when required=False."""
    field = FIELD_FACTORY.create_field(
        type_str="enum",
        name="mode",
        description="enum test",
        values=["auto", "manual"],
        default="manual",
        required=False
    )
    assert field.default == "manual"

def test_enum_default_without_required_false():
    """Providing a default without required=False should raise FormatError."""
    with pytest.raises(FormatError):
        FIELD_FACTORY.create_field(
            type_str="enum",
            name="mode",
            description="enum test",
            values=["on", "off"],
            default="on"
        )

def test_enum_default_value_not_in_choices():
    """Providing a default not in values list should raise ValidationError later."""
    with pytest.raises(FormatError):
        field = FIELD_FACTORY.create_field(
            type_str="enum",
            name="mode",
            description="enum test",
            values=["x", "y"],
            default="z",
            required=False
        )
        field.validate_and_build("z")

# -----------------------------
# Tuple Support
# -----------------------------

def test_enum_values_as_tuple():
    """EnumField should accept values as a tuple."""
    field = FIELD_FACTORY.create_field(
        type_str="enum",
        name="size",
        description="enum test",
        values=("S", "M", "L")
    )
    assert isinstance(field, EnumField)
