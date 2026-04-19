import pytest

from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.schema import Schema


class BasicUser:
    def __init__(self, name: str, age: int = 18):
        self.name = name
        self.age = age


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


class Vehicle:
    def __init__(self, model: str):
        self.model = model


def _basic_user_class_path() -> str:
    return "tests.schemas.base.test_object_field_file_configs.BasicUser"


def _with_kwargs_class_path() -> str:
    return "tests.schemas.base.test_object_field_file_configs.WithKwargs"


def _scalar_class_path() -> str:
    return "tests.schemas.base.test_object_field_file_configs.BuildFromScalar"


def _animal_class_path() -> str:
    return "tests.schemas.base.test_object_field_file_configs.Animal"


def _dog_class_path() -> str:
    return "tests.schemas.base.test_object_field_file_configs.Dog"


def _vehicle_class_path() -> str:
    return "tests.schemas.base.test_object_field_file_configs.Vehicle"


def _required_object_schema_yaml(class_path: str) -> str:
    return f"""
        user:
          type: object[{class_path}]
          description: User object
          required: true
    """


def _optional_object_schema_yaml_with_default(class_path: str, default_yaml: str) -> str:
    return f"""
        user:
          type: object[{class_path}]
          description: User object
          required: false
          default:
{default_yaml}
    """


def test_object_required_builds_instance_from_mapping(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": _required_object_schema_yaml(_basic_user_class_path()),
            "config.yaml": """
                user:
                  name: Alice
                  age: 33
            """,
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert isinstance(built["user"], BasicUser)
    assert built["user"].name == "Alice"
    assert built["user"].age == 33
    assert data_with_default["user"] == {"name": "Alice", "age": 33}


def test_object_required_missing_field_rejected(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": _required_object_schema_yaml(_basic_user_class_path()),
            "config.yaml": "{}",
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    with pytest.raises(ValidationError, match="Missing required field 'user'"):
        schema.validate_file(files["config.yaml"])


def test_object_required_rejects_unexpected_keys_without_kwargs(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": _required_object_schema_yaml(_basic_user_class_path()),
            "config.yaml": """
                user:
                  name: Alice
                  age: 33
                  extra: no
            """,
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    with pytest.raises(ValidationError, match="Unexpected keys:"):
        schema.validate_file(files["config.yaml"])


def test_object_required_allows_extra_keys_with_kwargs_constructor(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": _required_object_schema_yaml(_with_kwargs_class_path()),
            "config.yaml": """
                user:
                  name: Alice
                  a: 1
                  b: two
            """,
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, _ = schema.validate_file(files["config.yaml"])

    assert isinstance(built["user"], WithKwargs)
    assert built["user"].name == "Alice"
    assert built["user"].extra == {"a": 1, "b": "two"}


def test_object_required_supports_subclass_resolution_via_type_sentinel(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": _required_object_schema_yaml(_animal_class_path()),
            "config.yaml": f"""
                user:
                  _type_: {_dog_class_path()}
                  name: Rex
                  breed: Labrador
            """,
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, _ = schema.validate_file(files["config.yaml"])

    assert isinstance(built["user"], Dog)
    assert built["user"].name == "Rex"
    assert built["user"].breed == "Labrador"


def test_object_required_rejects_non_subclass_type_sentinel(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": _required_object_schema_yaml(_animal_class_path()),
            "config.yaml": f"""
                user:
                  _type_: {_vehicle_class_path()}
                  model: Roadster
            """,
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    with pytest.raises(ValidationError, match="is not a subclass"):
        schema.validate_file(files["config.yaml"])


def test_object_optional_missing_field_uses_default_instance(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": _optional_object_schema_yaml_with_default(
                _basic_user_class_path(),
                "            name: Bob\n            age: 20",
            ),
            "config.yaml": "{}",
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert isinstance(built["user"], BasicUser)
    assert built["user"].name == "Bob"
    assert built["user"].age == 20
    assert isinstance(data_with_default["user"], BasicUser)
    assert data_with_default["user"].name == "Bob"


def test_object_optional_provided_value_overrides_default(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": _optional_object_schema_yaml_with_default(
                _basic_user_class_path(),
                "            name: Bob\n            age: 20",
            ),
            "config.yaml": """
                user:
                  name: Carol
                  age: 44
            """,
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert isinstance(built["user"], BasicUser)
    assert built["user"].name == "Carol"
    assert built["user"].age == 44
    assert data_with_default["user"] == {"name": "Carol", "age": 44}


def test_object_optional_without_default_rejected(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": _required_object_schema_yaml(_basic_user_class_path()).replace(
                "required: true", "required: false"
            ),
            "config.yaml": "{}",
        }
    )

    with pytest.raises(ValidationError, match="invalid default value"):
        Schema.from_yaml(str(files["schema.yaml"]))


def test_object_required_accepts_scalar_when_constructor_supports_it(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": _required_object_schema_yaml(_scalar_class_path()),
            "config.yaml": "user: 5",
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert isinstance(built["user"], BuildFromScalar)
    assert built["user"].value == 5
    assert data_with_default["user"] == 5
