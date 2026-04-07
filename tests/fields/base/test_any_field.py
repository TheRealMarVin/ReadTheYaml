import pytest

from readtheyaml.exceptions.format_error import FormatError
from readtheyaml.fields.base.any_field import AnyField
from readtheyaml.schema import Schema


@pytest.mark.parametrize("value", [None, "hello", 42, 3.14, {"k": "v"}])
def test_any_field_accepts_all_supported_value_shapes(value):
    """AnyField should pass through None, str, int, float, and object values."""
    field = AnyField(name="anything", description="accepts anything")
    assert field.validate_and_build(value) == value


def test_any_field_optional_with_none_default():
    """Optional AnyField should allow None as default."""
    field = AnyField(name="anything", description="optional any", required=False, default=None)
    assert field.required is False
    assert field.default is None


@pytest.mark.parametrize("default", ["hello", 42, 3.14, {"nested": {"x": 1}}])
def test_any_field_optional_with_typed_defaults(default):
    """Optional AnyField should preserve defaults of supported non-None types."""
    field = AnyField(name="anything", description="optional any", required=False, default=default)
    assert field.default == default


def test_any_field_required_rejects_default():
    """AnyField should reject defaults when required=True."""
    with pytest.raises(FormatError, match="default value for a required field"):
        AnyField(name="anything", description="required any", required=True, default="x")


def test_schema_optional_any_field_missing_uses_none_default():
    """Schema should inject None when optional AnyField is missing and default=None."""
    schema = Schema(
        name="root",
        fields={"anything": AnyField(name="anything", description="optional any", required=False, default=None)}
    )

    built, data_with_default = schema.build_and_validate({})
    assert built["anything"] is None
    assert data_with_default["anything"] is None


@pytest.mark.parametrize("default", ["hello", 42, 3.14, {"nested": {"x": 1}}])
def test_schema_optional_any_field_missing_uses_typed_defaults(default):
    """Schema should inject the configured default for optional AnyField."""
    schema = Schema(
        name="root",
        fields={"anything": AnyField(name="anything",description="optional any", required=False, default=default)}
    )

    built, data_with_default = schema.build_and_validate({})
    assert built["anything"] == default
    assert data_with_default["anything"] == default
