import pytest
from readtheyaml.fields.field_factory import FIELD_FACTORY


def test_factory_rejects_empty_string():
    """Test that empty string is rejected by the factory."""
    with pytest.raises(ValueError, match="Unknown field type"):
        FIELD_FACTORY.create_field("", name="my_field", description="test field")