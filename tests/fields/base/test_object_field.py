import pytest

from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.fields.base.any_field import AnyField
from readtheyaml.fields.base.numerical_field import NumericalField
from readtheyaml.fields.base.object_field import ObjectField
from readtheyaml.fields.field_factory import FIELD_FACTORY
from readtheyaml.schema import Schema


class SimpleUser:
    def __init__(self, name: str, age: int = 18):
        self.name = name
        self.age = age


class MixedHintsUser:
    def __init__(self, name, age: int):
        self.name = name
        self.age = age


class OptionalNicknameUser:
    def __init__(self, name: str, nickname: str | None = None):
        self.name = name
        self.nickname = nickname


class WithKwargs:
    def __init__(self, name: str, **kwargs):
        self.name = name
        self.extra = kwargs


class BuildFromScalar:
    def __init__(self, value: int):
        if not isinstance(value, int):
            raise TypeError("value must be int")
        self.value = value


class Animal:
    def __init__(self, name: str):
        self.name = name


class Dog(Animal):
    def __init__(self, name: str, breed: str = "mixed"):
        super().__init__(name)
        self.breed = breed


class Car:
    def __init__(self, model: str):
        self.model = model


def test_object_field_builds_object_from_dict_with_fixed_class_path():
    field = ObjectField(name="user", description="user object", factory=FIELD_FACTORY, class_path="tests.fields.base.test_object_field.SimpleUser")

    result = field.validate_and_build({"name": "Alice", "age": 33})
    assert isinstance(result, SimpleUser)
    assert result.name == "Alice"
    assert result.age == 33


def test_object_field_uses_optional_constructor_default_when_missing():
    field = ObjectField(name="user", description="user object", factory=FIELD_FACTORY, class_path="tests.fields.base.test_object_field.SimpleUser")

    result = field.validate_and_build({"name": "Alice"})
    assert isinstance(result, SimpleUser)
    assert result.age == 18


def test_object_field_uses_anyfield_for_untyped_constructor_params():
    field = ObjectField(
        name="user",
        description="user object",
        factory=FIELD_FACTORY,
        class_path="tests.fields.base.test_object_field.MixedHintsUser",
    )

    assert isinstance(field.subfields["name"], AnyField)


def test_object_field_uses_typed_field_for_typed_constructor_params():
    field = ObjectField(
        name="user",
        description="user object",
        factory=FIELD_FACTORY,
        class_path="tests.fields.base.test_object_field.MixedHintsUser",
    )

    assert isinstance(field.subfields["age"], NumericalField)


def test_object_field_validates_optional_parameter_type():
    field = ObjectField(name="user", description="user object", factory=FIELD_FACTORY, class_path="tests.fields.base.test_object_field.OptionalNicknameUser")

    with pytest.raises(ValidationError, match=r"Field 'user\.nickname':"):
        field.validate_and_build({"name": "Alice", "nickname": 42})


def test_object_field_rejects_unexpected_keys_when_no_kwargs_in_constructor():
    field = ObjectField(name="user", description="user object", factory=FIELD_FACTORY, class_path="tests.fields.base.test_object_field.SimpleUser")

    with pytest.raises(ValidationError, match=r"Field 'user': Unexpected keys: \['unknown'\]"):
        field.validate_and_build({"name": "Alice", "unknown": "x"})


def test_object_field_allows_extra_keys_when_constructor_accepts_kwargs():
    field = ObjectField(name="user", description="user object", factory=FIELD_FACTORY, class_path="tests.fields.base.test_object_field.WithKwargs")

    result = field.validate_and_build({"name": "Alice", "a": 1, "b": 2})
    assert isinstance(result, WithKwargs)
    assert result.extra == {"a": 1, "b": 2}


def test_object_field_allows_derived_class_when_base_class_is_configured():
    field = ObjectField(name="animal", description="animal object", factory=FIELD_FACTORY, class_path="tests.fields.base.test_object_field.Animal")

    result = field.validate_and_build({"_type_": "tests.fields.base.test_object_field.Dog", "name": "Rex", "breed": "Labrador"})
    assert isinstance(result, Dog)
    assert result.name == "Rex"
    assert result.breed == "Labrador"


def test_object_field_rejects_non_subclass_when_base_class_is_configured():
    field = ObjectField(name="animal", description="animal object", factory=FIELD_FACTORY, class_path="tests.fields.base.test_object_field.Animal")

    with pytest.raises(ValidationError, match=r"Field 'animal': 'tests\.fields\.base\.test_object_field\.Car' is not a subclass of 'tests\.fields\.base\.test_object_field\.Animal'"):
        field.validate_and_build({"_type_": "tests.fields.base.test_object_field.Car", "model": "Roadster"})


def test_object_field_requires_type_sentinel_when_class_is_not_fixed():
    field = ObjectField(name="obj", description="dynamic object", factory=FIELD_FACTORY)

    with pytest.raises(ValidationError, match=r"Field 'obj': Missing '_type_' key to resolve object type"):
        field.validate_and_build({"name": "Alice"})


def test_object_field_resolves_dynamic_type_and_builds_instance():
    field = ObjectField(name="obj", description="dynamic object", factory=FIELD_FACTORY)

    result = field.validate_and_build({"_type_": "tests.fields.base.test_object_field.SimpleUser", "name": "Alice", "age": 25})
    assert isinstance(result, SimpleUser)
    assert result.age == 25


def test_object_field_rejects_non_dict_when_no_fixed_class():
    field = ObjectField(name="obj", description="dynamic object", factory=FIELD_FACTORY)

    with pytest.raises(ValidationError, match="Expected a dictionary to instantiate object"):
        field.validate_and_build("not-a-dict")


def test_object_field_non_dict_for_fixed_class_raises_wrapped_constructor_error():
    field = ObjectField(name="obj", description="fixed object", factory=FIELD_FACTORY, class_path="tests.fields.base.test_object_field.BuildFromScalar")

    with pytest.raises(ValidationError, match=r"Field 'obj': Failed to create 'tests\.fields\.base\.test_object_field\.BuildFromScalar': value must be int",):
        field.validate_and_build("not-an-int")


def test_object_field_from_type_string_object_syntax():
    field = ObjectField.from_type_string(type_str="object[tests.fields.base.test_object_field.SimpleUser]", name="user", factory=FIELD_FACTORY, description="user object")

    assert isinstance(field, ObjectField)
    assert field.class_path == "tests.fields.base.test_object_field.SimpleUser"


def test_object_field_from_type_string_dotted_path_syntax():
    field = ObjectField.from_type_string(type_str="tests.fields.base.test_object_field.SimpleUser", name="user", factory=FIELD_FACTORY, description="user object")

    assert isinstance(field, ObjectField)
    assert field.class_path == "tests.fields.base.test_object_field.SimpleUser"


def test_object_field_from_type_string_returns_none_for_non_object_type():
    field = ObjectField.from_type_string(type_str="str", name="user", factory=FIELD_FACTORY, description="user object")
    assert field is None


def test_schema_can_declare_base_object_type_and_build_derived_instance():
    schema = Schema._from_dict({"pet": {"type": "object[tests.fields.base.test_object_field.Animal]", "description": "animal object"}})

    built, _ = schema.build_and_validate({"pet": {"_type_": "tests.fields.base.test_object_field.Dog", "name": "Max", "breed": "Husky"}})
    assert isinstance(built["pet"], Dog)
    assert built["pet"].name == "Max"
    assert built["pet"].breed == "Husky"
