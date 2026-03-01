import pytest
from readtheyaml.fields.base.none_field import NoneField
from readtheyaml.fields.field_factory import FIELD_FACTORY


def test_factory_accepts_None():
    """Test that 'None' is accepted by the factory."""
    field = FIELD_FACTORY.create_field("None", name="my_field", description="test field")
    assert isinstance(field, NoneField)


def test_factory_accepts_none_lowercase():
    """Test that 'none' (lowercase) is accepted by the factory."""
    field = FIELD_FACTORY.create_field("none", name="my_field", description="test field")
    assert isinstance(field, NoneField)


def test_factory_accepts_NONE_uppercase():
    """Test that 'NONE' (uppercase) is accepted by the factory."""
    field = FIELD_FACTORY.create_field("NONE", name="my_field", description="test field")
    assert isinstance(field, NoneField)


def test_factory_rejects_mixed_case_noNE():
    """Test that mixed case like 'noNE' is rejected by the factory."""
    with pytest.raises(ValueError, match="Unknown field type"):
        FIELD_FACTORY.create_field("noNE", name="my_field", description="test field")


def test_factory_rejects_random_string():
    """Test that unrelated string like 'null' is rejected by the factory."""
    with pytest.raises(ValueError, match="Unknown field type"):
        FIELD_FACTORY.create_field("null", name="my_field", description="test field")

###
def test_none_field_initialization():
    """Test that NoneField is properly initialized."""
    field = NoneField(name="new_field", description="My description", required=False, default=None)
    assert field.name == "new_field"
    assert field.description == "My description"
    assert not field.required

def test_none_field_validate_uppercase_none():
    """Test validation of string 'None' as None."""
    field = NoneField(name="new_field", description="My description", required=False, default=None)
    assert field.validate_and_build("None") is None

def test_none_field_validate_lowercase_none():
    """Test validation of string 'none' as None."""
    field = NoneField(name="new_field", description="My description", required=False, default=None)
    assert field.validate_and_build("none") is None

def test_none_field_validate_actual_none():
    """Test validation of actual None value."""
    field = NoneField(name="new_field", description="My description", required=False, default=None)
    assert field.validate_and_build(None) is None

def test_none_field_rejects_empty_string():
    """Test rejection of empty string input."""
    field = NoneField(name="new_field", description="My description", required=False, default=None)
    with pytest.raises(ValidationError, match="must be null/None"):
        field.validate_and_build("")

def test_none_field_rejects_numeric_string():
    """Test rejection of numeric string input."""
    field = NoneField(name="new_field", description="My description", required=False, default=None)
    with pytest.raises(ValidationError, match="must be null/None"):
        field.validate_and_build("123")

def test_none_field_rejects_integer():
    """Test rejection of integer input."""
    field = NoneField(name="new_field", description="My description", required=False, default=None)
    with pytest.raises(ValidationError, match="must be null/None"):
        field.validate_and_build(123)

def test_none_field_accepts_string_default():
    """Test field initialization with string 'None' as default."""
    field = NoneField(name="new_field", description="My description", required=False, default="None")
    assert field.default == None

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