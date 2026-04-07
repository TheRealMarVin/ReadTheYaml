import pytest

from readtheyaml.exceptions.format_error import FormatError
from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.fields.base.bool_field import BoolField
from readtheyaml.fields.field_factory import FIELD_FACTORY


@pytest.mark.parametrize("type_name", ["bool", "BOOL", "Bool"])
def test_factory_accepts_supported_bool_type_names(type_name):
    """Factory should accept supported bool type spellings."""
    field = FIELD_FACTORY.create_field(type_name, name="my_field", description="test field")
    assert isinstance(field, BoolField)


@pytest.mark.parametrize("type_name", ["boOL", "boolean", "BoOl", "Boolean"])
def test_factory_rejects_unsupported_bool_type_names(type_name):
    """Factory should reject unsupported bool-like type names."""
    with pytest.raises(ValueError):
        FIELD_FACTORY.create_field(type_name, name="my_field", description="test field")


@pytest.mark.parametrize(
    ("default_value", "expected"),
    [(True, True), ("True", True), (False, False), ("False", False)],
)
def test_factory_bool_valid_defaults(default_value, expected):
    """Factory should normalize valid bool defaults."""
    field = FIELD_FACTORY.create_field(
        "bool", name="my_field", description="test field", required=False, default=default_value
    )
    assert field.default is expected


@pytest.mark.parametrize("invalid_default", [None, "", "yes", 0, 1, 12.5])
def test_factory_bool_invalid_defaults(invalid_default):
    """Factory should reject invalid bool defaults."""
    with pytest.raises(FormatError, match="invalid default value"):
        FIELD_FACTORY.create_field(
            "bool", name="my_field", description="test field", required=False, default=invalid_default
        )


def test_validate_bool_true():
    """Boolean True values should validate unchanged."""
    field = BoolField(name="new_field", description="My description", required=False, default=True)
    assert field.name == "new_field" and field.description == "My description" and not field.required
    assert field.validate_and_build(True) is True


@pytest.mark.parametrize("value", ["TRUE", "True", "tRuE", "true"])
def test_validate_bool_case_insensitive_true_strings(value):
    field = BoolField(name="new_field", description="Case insensitive true test")
    assert field.validate_and_build(value) is True


@pytest.mark.parametrize("value", ["FALSE", "False", "fAlSe", "false"])
def test_validate_bool_case_insensitive_false_strings(value):
    field = BoolField(name="new_field", description="Case insensitive false test")
    assert field.validate_and_build(value) is False


def test_validate_bool_false():
    """Boolean False values should validate unchanged."""
    field = BoolField(name="new_field", description="My description", required=False, default=True)
    assert field.validate_and_build(False) is False


@pytest.mark.parametrize("value", ["", "none", "None", "NONE", "null", "Null", "NULL"])
def test_validate_bool_rejects_none_null_or_empty_strings(value):
    field = BoolField(name="new_field", description="None/Null/Empty string test")
    with pytest.raises(ValidationError, match="contains None or null or empty"):
        field.validate_and_build(value)


@pytest.mark.parametrize("value", [123, 12.5, [], {}, object()])
def test_validate_bool_rejects_non_bool_non_string_types(value):
    field = BoolField(name="new_field", description="Type mismatch test")
    with pytest.raises(ValidationError, match=r"Expected a boolean value, got "):
        field.validate_and_build(value)


def test_validate_bool_rejects_none_type():
    field = BoolField(name="new_field", description="None value test")
    with pytest.raises(ValidationError, match="Expected a boolean value, got NoneType"):
        field.validate_and_build(None)


@pytest.mark.parametrize(
    "value",
    ["123", "yes", "no", "on", "off", "1", "0", "y", "n", " true ", "\ttrue\n", "false\t", "  false  "],
)
def test_validate_bool_rejects_invalid_string_variants(value):
    field = BoolField(name="new_field", description="Invalid string variants test")
    with pytest.raises(ValidationError, match=r"Expected a boolean value\."):
        field.validate_and_build(value)
