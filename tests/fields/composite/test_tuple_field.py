from functools import partial

import pytest

from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.fields.composite.list_field import ListField
from readtheyaml.fields.base.numerical_field import NumericalField
from readtheyaml.fields.base.string_field import StringField
from readtheyaml.fields.base.bool_field import BoolField
from readtheyaml.fields.base.object_field import ObjectField
from readtheyaml.fields.field_factory import FIELD_FACTORY
from readtheyaml.fields.composite.tuple_field import TupleField


def test_required_tuple_field():
    """Test that a required TupleField is properly initialized without a default."""
    field = TupleField(
        name="test_tuple",
        description="Test tuple",
        required=True,
        element_fields=[
            partial(StringField),
            partial(NumericalField, value_type=int)
        ]
    )
    assert field.name == "test_tuple"
    assert field.description == "Test tuple"
    assert field.required
    assert field.default is None
    assert len(field._slots) == 2


def test_optional_tuple_field_with_default():
    """Test that an optional TupleField can be initialized with a default value."""
    default_value = ("John", 30)
    field = TupleField(
        name="test_tuple",
        description="Test tuple",
        required=False,
        default=default_value,
        element_fields=[
            partial(StringField),
            partial(NumericalField, value_type=int)
        ]
    )
    assert field.name == "test_tuple"
    assert field.description == "Test tuple"
    assert not field.required
    assert field.default == default_value
    assert len(field._slots) == 2


def test_validate_tuple_with_correct_types():
    """Test that TupleField validates a tuple with correct types."""
    field = TupleField(
        name="person",
        description="Test tuple",
        element_fields=[
            partial(StringField),
            partial(NumericalField, value_type=int),
            partial(BoolField)
        ]
    )

    # Test valid tuple
    result = field.validate_and_build(("John Doe", 30, True))
    assert result == ("John Doe", 30, True)


def test_validate_tuple_with_string_representation():
    """Test that TupleField can parse a string representation of a tuple."""
    field = TupleField(
        name="coordinates",
        description="Test tuple",
        element_fields=[
            partial(NumericalField, value_type=float, name="x", description="X coordinate"),
            partial(NumericalField, value_type=float, name="y", description="Y coordinate")
        ]
    )

    # Test with string representation
    result = field.validate_and_build("(3.14, 2.71)")
    assert result == (3.14, 2.71)


def test_validate_tuple_rejects_wrong_length():
    """Test that TupleField rejects tuples with the wrong length."""
    field = TupleField(
        name="coordinates",
        description="Test tuple",
        element_fields=[
            partial(NumericalField, value_type=float, name="x", description="X coordinate"),
            partial(NumericalField, value_type=float, name="y", description="Y coordinate")
        ]
    )

    # Test with too few elements
    with pytest.raises(ValidationError, match="must contain exactly 2 elements"):
        field.validate_and_build((1.0,))

    # Test with too many elements
    with pytest.raises(ValidationError, match="must contain exactly 2 elements"):
        field.validate_and_build((1.0, 2.0, 3.0))


def test_validate_tuple_rejects_invalid_types():
    """Test that TupleField rejects elements with invalid types."""
    field = TupleField(
        name="person",
        description="Test tuple",
        element_fields=[
            partial(StringField, name="name", description="Name"),
            partial(NumericalField, value_type=int, name="age", description="Age")
        ]
    )

    # Test with invalid type in second element
    with pytest.raises(ValidationError, match="Tuple element 1 invalid"):
        field.validate_and_build(("John Doe", "thirty"))  # Age should be an int


def test_validate_tuple_with_nested_structures():
    """Test that TupleField works with nested structures."""
    field = TupleField(
        name="nested",
        description="Test tuple",
        element_fields=[
            partial(ListField, name="numbers", description="numbers",
                    item_field=partial(NumericalField, value_type=int, name="num", description="Val")),
            partial(StringField, name="name", description="Name", cast_to_string=False)
        ]
    )

    # Test with a valid nested structure
    result = field.validate_and_build(([1, 2, 3], "test"))
    assert result == ([1, 2, 3], "test")

    # Test with an invalid nested structure
    with pytest.raises(ValidationError, match="Tuple element 0 invalid"):
        field.validate_and_build(([1, "two", 3], "test"))  # Non-int in a list


def test_validate_tuple_rejects_none():
    """Test that TupleField rejects None as a value."""
    field = TupleField(
        name="test",
        description="Test tuple",
        element_fields=[
            partial(StringField, name="name", description="Name")
        ]
    )

    with pytest.raises(ValidationError, match="None is not a valid tuple"):
        field.validate_and_build(None)


def test_validate_tuple_rejects_non_string_non_tuple_input():
    """Test that TupleField rejects non-string/non-tuple inputs without crashing."""
    field = TupleField(
        name="test",
        description="Test tuple",
        element_fields=[
            partial(StringField, name="name", description="Name")
        ]
    )

    with pytest.raises(ValidationError, match="Not a valid tuple"):
        field.validate_and_build({"name": "Alice"})


class TuplePerson:
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age


class TuplePet:
    def __init__(self, kind: str):
        self.kind = kind


class BaseTupleAnimal:
    def __init__(self, name: str):
        self.name = name


class TupleDog(BaseTupleAnimal):
    def __init__(self, name: str, breed: str):
        super().__init__(name)
        self.breed = breed


class TupleCat(BaseTupleAnimal):
    def __init__(self, name: str, lives: int = 9):
        super().__init__(name)
        self.lives = lives


class TupleCar:
    def __init__(self, model: str):
        self.model = model


def test_validate_tuple_of_various_objects():
    """TupleField should validate tuples containing different object types."""
    field = TupleField(
        name="mixed_objects_tuple",
        description="Tuple of various objects",
        element_fields=[
            partial(ObjectField, factory=FIELD_FACTORY),
            partial(ObjectField, factory=FIELD_FACTORY),
        ],
    )

    value = (
        {"_type_": "tests.fields.composite.test_tuple_field.TuplePerson", "name": "Alice", "age": 30},
        {"_type_": "tests.fields.composite.test_tuple_field.TuplePet", "kind": "cat"},
    )
    assert field.validate_and_build(value) == value


def test_validate_tuple_of_objects_deriving_from_base_class():
    """TupleField should validate derived object types when ObjectField uses a base class."""
    field = TupleField(
        name="animals_tuple",
        description="Tuple of animals",
        element_fields=[
            partial(
                ObjectField,
                factory=FIELD_FACTORY,
                class_path="tests.fields.composite.test_tuple_field.BaseTupleAnimal",
            ),
            partial(
                ObjectField,
                factory=FIELD_FACTORY,
                class_path="tests.fields.composite.test_tuple_field.BaseTupleAnimal",
            ),
        ],
    )

    value = (
        {"_type_": "tests.fields.composite.test_tuple_field.TupleDog", "name": "Rex", "breed": "Labrador"},
        {"_type_": "tests.fields.composite.test_tuple_field.TupleCat", "name": "Mittens", "lives": 7},
    )
    assert field.validate_and_build(value) == value


def test_validate_tuple_rejects_non_subclass_for_base_class_object_field():
    """TupleField should reject tuple elements whose _type_ is not a subclass of configured base class."""
    field = TupleField(
        name="animals_tuple",
        description="Tuple of animals",
        element_fields=[
            partial(
                ObjectField,
                factory=FIELD_FACTORY,
                class_path="tests.fields.composite.test_tuple_field.BaseTupleAnimal",
            ),
            partial(
                ObjectField,
                factory=FIELD_FACTORY,
                class_path="tests.fields.composite.test_tuple_field.BaseTupleAnimal",
            ),
        ],
    )

    with pytest.raises(ValidationError, match="Tuple element 0 invalid"):
        field.validate_and_build(
            (
                {"_type_": "tests.fields.composite.test_tuple_field.TupleCar", "model": "Roadster"},
                {"_type_": "tests.fields.composite.test_tuple_field.TupleCat", "name": "Mittens"},
            )
        )
