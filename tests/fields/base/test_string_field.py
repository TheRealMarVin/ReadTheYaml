import pytest
from readtheyaml.fields.base.string_field import StringField
from readtheyaml.fields.field_factory import FIELD_FACTORY
from readtheyaml.exceptions.format_error import FormatError
from readtheyaml.exceptions.validation_error import ValidationError

# -----------------------------
# Field Creation
# -----------------------------

@pytest.mark.parametrize("casing", ["str", "Str", "STR"])
def test_string_type_valid_casing(casing):
    """Factory should accept 'str', 'Str', and 'STR'."""
    field = FIELD_FACTORY.create_field(
        type_str=casing,
        name="my_str",
        description="test string"
    )
    assert isinstance(field, StringField)

def test_string_type_invalid_casing():
    """Factory should reject incorrectly cased string types."""
    for invalid in ["stR", "sttr", "string"]:
        with pytest.raises(ValueError):
            FIELD_FACTORY.create_field(
                type_str=invalid,
                name="my_str",
                description="test",
                required=False
            )

# -----------------------------
# Constructor Format Validation
# -----------------------------

def test_string_invalid_min_length():
    """StringField should raise FormatError if min_length < 0."""
    with pytest.raises(FormatError):
        StringField(name="s1", description="", min_length=-1)

def test_string_invalid_max_length():
    """StringField should raise FormatError if max_length < min_length."""
    with pytest.raises(FormatError):
        StringField(name="s2", description="", min_length=5, max_length=3)

# -----------------------------
# Value Validation
# -----------------------------

def test_string_valid_input():
    """StringField should accept valid strings within length limits."""
    field = StringField(name="s", description="", min_length=2, max_length=5)
    assert field.validate_and_build("abc") == "abc"

def test_string_too_short():
    """StringField should raise ValidationError for too-short strings."""
    field = StringField(name="s", description="", min_length=3)
    with pytest.raises(ValidationError):
        field.validate_and_build("hi")

def test_string_too_long():
    """StringField should raise ValidationError for too-long strings."""
    field = StringField(name="s", description="", max_length=4)
    with pytest.raises(ValidationError):
        field.validate_and_build("hello")

def test_string_cast_to_string_enabled():
    """StringField should cast non-string values to string when enabled."""
    field = StringField(name="s", description="", cast_to_string=True)
    assert field.validate_and_build(1234) == "1234"

def test_string_cast_to_string_disabled():
    """StringField should reject non-string values when casting is disabled."""
    field = StringField(name="s", description="", cast_to_string=False)
    with pytest.raises(ValidationError):
        field.validate_and_build(1234)

# -----------------------------
# Default Value Handling
# -----------------------------

def test_string_valid_default():
    """Factory should accept valid default when required=False."""
    field = FIELD_FACTORY.create_field(
        type_str="str",
        name="opt",
        description="",
        required=False,
        default="default value"
    )
    assert field.default == "default value"

def test_string_default_without_required_false():
    """Providing a default without required=False should raise FormatError."""
    with pytest.raises(FormatError):
        FIELD_FACTORY.create_field(
            type_str="str",
            name="bad",
            description="",
            default="oops"
        )

def test_string_default_too_short():
    """Default shorter than min_length should raise ValidationError."""
    with pytest.raises(FormatError):
        field = FIELD_FACTORY.create_field(
            type_str="str",
            name="s",
            description="",
            min_length=5,
            required=False,
            default="abc"
        )
        field.validate_and_build("abc")

def test_string_default_too_long():
    """Default longer than max_length should raise ValidationError."""
    with pytest.raises(FormatError):
        field = FIELD_FACTORY.create_field(
            type_str="str",
            name="s",
            description="",
            max_length=2,
            required=False,
            default="abc"
        )
        field.validate_and_build("abc")
