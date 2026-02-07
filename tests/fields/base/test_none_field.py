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
