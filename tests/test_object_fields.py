import pytest

from readtheyaml.fields.field_helpers import _parse_field_type
from readtheyaml.fields.base.object_field import ObjectField
from readtheyaml.exceptions.validation_error import ValidationError


class DummyNoParams:
    def __init__(self):
        self.ok = True


class DummyWithParams:
    def __init__(self, a, b):
        self.a = a
        self.b = b


class DummyWithDefaults:
    def __init__(self, a, b=2):
        self.a = a
        self.b = b


class DummyWithTypeHints:
    def __init__(self, a: int, b: str):

        self.a = a
        self.b = b


class DummyWithKwargs:
    def __init__(self, a, **kwargs):
        self.a = a
        self.extra = kwargs


def test_object_field_no_params():
    """Test creating an object with a no-argument constructor."""
    field = ObjectField(factory=_parse_field_type, class_path=f"{__name__}.DummyNoParams", name="obj", description="dummy")
    built = field.validate_and_build({})
    assert isinstance(built, DummyNoParams)
    assert built.ok is True


def test_object_field_with_params():
    """Test creating an object with required constructor parameters."""
    field = ObjectField(factory=_parse_field_type, class_path=f"{__name__}.DummyWithParams", name="obj", description="dummy")
    built = field.validate_and_build({"a": 1, "b": 2})
    assert isinstance(built, DummyWithParams)
    assert built.a == 1 and built.b == 2


def test_object_field_with_defaults():
    """Test creating an object where some parameters have default values."""
    field = ObjectField(factory=_parse_field_type, class_path=f"{__name__}.DummyWithDefaults", name="obj", description="dummy")
    built = field.validate_and_build({"a": 10})
    assert isinstance(built, DummyWithDefaults)
    assert built.a == 10 and built.b == 2


def test_object_field_with_type_hints():
    """Test object creation with type hints in __init__, no enforcement at runtime."""
    field = ObjectField(factory=_parse_field_type, class_path=f"{__name__}.DummyWithTypeHints", name="obj", description="dummy")
    built = field.validate_and_build({"a": 42, "b": "hello"})
    assert isinstance(built, DummyWithTypeHints)
    assert built.a == 42 and built.b == "hello"


def test_object_field_accepts_prebuilt():
    """Test that pre-built object is passed through as-is."""
    field = ObjectField(factory=_parse_field_type, class_path=f"{__name__}.DummyWithParams", name="obj", description="dummy")
    obj = DummyWithParams(1, 2)
    result = field.validate_and_build(obj.__dict__)  # simulate dictionary-based use
    assert isinstance(result, DummyWithParams)
    assert result.a == 1 and result.b == 2


def test_object_field_resolves_type_from_sentinel():
    """Test dynamic class resolution using _type_ key."""
    field = ObjectField(factory=_parse_field_type, name="obj", description="dummy")
    built = field.validate_and_build({"_type_": f"{__name__}.DummyWithParams", "a": 4, "b": 5})
    assert isinstance(built, DummyWithParams)
    assert built.a == 4 and built.b == 5


def test_object_field_kwargs_allowed():
    """Test that extra fields are allowed when class supports **kwargs."""
    field = ObjectField(factory=_parse_field_type, class_path=f"{__name__}.DummyWithKwargs", name="obj", description="dummy")
    built = field.validate_and_build({"a": 4, "extra1": 99, "extra2": True})
    assert isinstance(built, DummyWithKwargs)
    assert built.a == 4
    assert built.extra == {"extra1": 99, "extra2": True}


def test_object_field_kwargs_not_allowed_raises():
    """Test that extra fields raise ValidationError when class doesn't support **kwargs."""
    field = ObjectField(factory=_parse_field_type, class_path=f"{__name__}.DummyWithParams", name="obj", description="dummy")
    with pytest.raises(ValidationError, match="Unexpected keys"):
        field.validate_and_build({"a": 4, "b": 5, "extra": 99})


def test_object_field_typo_in_class_path():
    """Test that a typo in the class_path raises ValidationError."""

    with pytest.raises(ValidationError, match="Failed to import"):
        field = ObjectField(factory=_parse_field_type, class_path=f"{__name__}.NonExistent", name="obj",
                            description="dummy")
        field.validate_and_build({})


def test_object_field_invalid_argument_type():
    """Test that constructor fails if argument types are wrong (e.g., str instead of int)."""
    field = ObjectField(factory=_parse_field_type, class_path=f"{__name__}.DummyWithTypeHints",name="obj", description="dummy")
    with pytest.raises(ValidationError):
        field.validate_and_build({"a": "bad", "b": "value"})


def test_object_field_missing_required_param():
    """Test that missing required parameters raises ValidationError."""
    field = ObjectField(factory=_parse_field_type, class_path=f"{__name__}.DummyWithParams", name="obj", description="dummy")
    with pytest.raises(ValidationError, match="Failed to create"):
        field.validate_and_build({"a": 1})


def test_object_field_missing_type_key():
    """Test missing _type_ key when no class_path is given raises ValidationError."""
    field = ObjectField(factory=_parse_field_type, name="obj", description="dummy")
    with pytest.raises(ValidationError, match="Missing '_type_' key"):
        field.validate_and_build({"a": 1})


def test_object_field_input_not_dict():
    """Test that non-dict input raises ValidationError if no class_path is set."""
    field = ObjectField(factory=_parse_field_type, name="obj", description="dummy")
    with pytest.raises(ValidationError, match="Expected a dictionary"):
        field.validate_and_build("not a dict")


def test_object_field_invalid_class_path_format():
    """Test invalid class path format (no module part) raises ValidationError."""
    with pytest.raises(ValidationError, match="Invalid class path"):
        field = ObjectField(factory=_parse_field_type, class_path="JustAClass", name="obj", description="dummy")
        field.validate_and_build({})


