import pytest

from readtheyaml.exceptions.format_error import FormatError
from readtheyaml.fields.base.bool_field import BoolField
from readtheyaml.fields.field_factory import FIELD_FACTORY


def test_factory_accepts_bool():
    """Test that 'bool' is accepted by the factory."""
    field = FIELD_FACTORY.create_field("bool", name="my_field", description="test field")
    assert isinstance(field, BoolField)


def test_factory_accepts_BOOL_uppercase():
    """Test that 'BOOL' is accepted by the factory."""
    field = FIELD_FACTORY.create_field("BOOL", name="my_field", description="test field")
    assert isinstance(field, BoolField)


def test_factory_accepts_Bool_capitalized():
    """Test that 'Bool' is accepted by the factory."""
    field = FIELD_FACTORY.create_field("Bool", name="my_field", description="test field")
    assert isinstance(field, BoolField)


def test_factory_rejects_mixed_case_boOL():
    """Test that mixed case like 'boOL' is rejected by the factory."""
    with pytest.raises(ValueError):
        FIELD_FACTORY.create_field("boOL", name="my_field", description="test field")


def test_factory_rejects_random_string_for_bool():
    """Test that unrelated string like 'boolean' is rejected by the factory."""
    with pytest.raises(ValueError):
        FIELD_FACTORY.create_field("boolean", name="my_field", description="test field")


def test_factory_bool_with_default_true():
    """Test that the 'bool' field supports default=True."""
    field = FIELD_FACTORY.create_field(
        "bool", name="my_field", description="test field", required=False, default=True
    )
    assert field.default is True

def test_factory_bool_with_default_true_string():
    """Test that the 'bool' field supports default=True."""
    field = FIELD_FACTORY.create_field(
        "bool", name="my_field", description="test field", required=False, default="True"
    )
    assert field.default is True


def test_factory_bool_with_default_false():
    """Test that the 'bool' field supports default=False."""
    field = FIELD_FACTORY.create_field(
        "bool", name="my_field", description="test field", required=False, default=False
    )
    assert field.default is False

def test_factory_bool_with_default_false_string():
    """Test that the 'bool' field supports default=False."""
    field = FIELD_FACTORY.create_field(
        "bool", name="my_field", description="test field", required=False, default="False"
    )
    assert field.default is False


def test_factory_bool_with_invalid_default_string():
    """Test that the 'bool' field rejects non-boolean default values."""
    with pytest.raises(FormatError):
        FIELD_FACTORY.create_field("bool", name="my_field", description="test field", required=False, default="yes")


def test_factory_bool_with_invalid_default_int():
    """Test that the 'bool' field rejects integer default values."""
    with pytest.raises(FormatError):
        FIELD_FACTORY.create_field("bool", name="my_field", description="test field", required=False, default=1)
