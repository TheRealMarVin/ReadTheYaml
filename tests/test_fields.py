import pytest

from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.fields.none_field import NoneField


# testing None
def test_valid_none():
    field = NoneField(name="new_field", description="My description", required=True, default=None)
    assert field.name == "new_field" and field.description == "My description" and field.required

    validated_val = field.validate("None")
    assert validated_val is None

    validated_val = field.validate("none")
    assert validated_val is None

    validated_val = field.validate(None)
    assert validated_val is None

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