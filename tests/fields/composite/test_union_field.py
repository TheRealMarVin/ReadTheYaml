from functools import partial

import pytest

from readtheyaml.exceptions.format_error import FormatError
from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.fields.composite.list_field import ListField
from readtheyaml.fields.base.numerical_field import NumericalField
from readtheyaml.fields.base.object_field import ObjectField
from readtheyaml.fields.base.string_field import StringField
from readtheyaml.fields.field_factory import FIELD_FACTORY
from readtheyaml.fields.composite.tuple_field import TupleField
from readtheyaml.fields.composite.union_field import UnionField


class UnionPerson:
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age


class UnionPet:
    def __init__(self, kind: str):
        self.kind = kind


class BaseUnionAnimal:
    def __init__(self, name: str):
        self.name = name


class UnionDog(BaseUnionAnimal):
    def __init__(self, name: str, breed: str):
        super().__init__(name)
        self.breed = breed


class UnionCat(BaseUnionAnimal):
    def __init__(self, name: str, lives: int = 9):
        super().__init__(name)
        self.lives = lives


class UnionCar:
    def __init__(self, model: str):
        self.model = model


def test_union_field_initialization():
    """Test that UnionField is properly initialized with options."""
    field = UnionField(
        name="test_union",
        description="Test union field",
        required=True,
        options=[
            partial(StringField, name="string_option", description="String option", cast_to_string=False),
            partial(NumericalField, value_type=int, name="int_option", description="Integer option")
        ]
    )
    assert field.name == "test_union"
    assert field.description == "Test union field"
    assert field.required
    assert len(field._options) == 2


def test_union_field_initialization_no_cast_in_string():
    """Test that UnionField is properly initialized with options with no cast for string."""
    field = UnionField(
        name="test_union",
        description="Test union field",
        required=True,
        options=[
            partial(StringField, name="string_option", description="String option"),
            partial(NumericalField, value_type=int, name="int_option", description="Integer option")
        ]
    )
    assert field.name == "test_union"
    assert field.description == "Test union field"
    assert field.required
    assert len(field._options) == 2


def test_union_field_initialization_no_name():
    """Test that UnionField is properly initialized with options when no names are provided"""
    field = UnionField(
        name="test_union",
        description="Test union field",
        required=True,
        options=[
            partial(StringField),
            partial(NumericalField, value_type=int)
        ]
    )
    assert field.name == "test_union"
    assert field.description == "Test union field"
    assert field.required
    assert len(field._options) == 2

def test_union_field_rejects_string_field_with_cast_to_string_true():
    """Test that UnionField rejects StringField with cast_to_string=True."""
    with pytest.raises(FormatError, match="StringField with cast_to_string=True is not allowed"):
        UnionField(
            name="test_union",
            description="Test invalid union field",
            options=[
                partial(StringField, name="string_option", description="String option", cast_to_string=True),
                partial(NumericalField, value_type=int, name="int_option", description="Integer option")
            ]
        )


def test_union_field_accepts_string_field_with_cast_to_string_false():
    """Test that UnionField accepts StringField with cast_to_string=False."""
    field = UnionField(
        name="test_union",
        description="Test valid union field",
        options=[
            partial(StringField, cast_to_string=False),
            partial(NumericalField, value_type=int)
        ]
    )
    assert len(field._options) == 2


def test_union_field_rejects_duplicate_list_field_types():
    """ListField entries are considered duplicate union option types, even with different item_field constraints."""
    with pytest.raises(FormatError, match="Duplicate field types found in UnionField"):
        UnionField(
            name="test_union",
            description="Test duplicate list field types",
            options=[
                partial(ListField, item_field=partial(NumericalField, value_type=int)),
                partial(ListField, item_field=partial(StringField, cast_to_string=False))
            ]
        )


def test_union_field_rejects_duplicate_tuple_field_types():
    """TupleField entries are considered duplicate union option types, even with different element definitions."""
    with pytest.raises(FormatError, match="Duplicate field types found in UnionField"):
        UnionField(
            name="test_union",
            description="Test duplicate tuple field types",
            options=[
                partial(TupleField, element_fields=[partial(StringField, cast_to_string=False)]),
                partial(TupleField, element_fields=[partial(NumericalField, value_type=int)])
            ]
        )


def test_union_field_rejects_duplicate_object_field_types():
    """ObjectField entries are considered duplicate union option types, even with different class_path values."""
    with pytest.raises(FormatError, match="Duplicate field types found in UnionField"):
        UnionField(
            name="test_union",
            description="Test duplicate object field types",
            options=[
                partial(
                    ObjectField,
                    factory=FIELD_FACTORY,
                    class_path="tests.fields.composite.test_union_field.UnionPerson"
                ),
                partial(
                    ObjectField,
                    factory=FIELD_FACTORY,
                    class_path="tests.fields.composite.test_union_field.UnionPet"
                )
            ]
        )


def test_union_field_rejects_duplicate_field_types():
    """Test that UnionField rejects duplicate field types in options."""
    with pytest.raises(FormatError, match="Duplicate field types found in UnionField"):
        UnionField(
            name="test_union",
            description="Test duplicate field types",
            options=[
                partial(NumericalField, value_type=int, name="int1", description="First int"),
                partial(NumericalField, value_type=float, name="float1", description="Float field"),
                partial(NumericalField, value_type=int, name="int2", description="Second int")
            ]
        )


def test_duplicate_check_ignores_different_parameters():
    """Test that UnionField considers field types with different parameters as duplicates."""
    with pytest.raises(FormatError, match="Duplicate field types found in UnionField"):
        UnionField(
            name="test_union",
            description="Test duplicate field types with different parameters",
            options=[
                partial(StringField, name="str1", description="First string", min_length=1),
                partial(NumericalField, value_type=int, name="int1", description="Integer field"),
                partial(StringField, name="str2", description="Second string", max_length=10)  # Still a duplicate
            ]
        )


def create_simple_union_field():
    """Helper function to create a UnionField with string and integer options."""
    return UnionField(
        name="test_union",
        description="Test union field",
        options=[
            partial(StringField),
            partial(NumericalField, value_type=int)
        ]
    )


def test_union_field_validates_string_option():
    """Test that UnionField validates string values when StringField is an option."""
    field = create_simple_union_field()
    assert field.validate_and_build("test") == "test"


def test_union_field_validates_int_option():
    """Test that UnionField validates integer values when NumericalField is an option."""
    field = create_simple_union_field()
    assert field.validate_and_build(42) == 42


def test_union_field_handles_numeric_strings_as_strings():
    """Test that UnionField treats numeric strings as strings when StringField is the first option."""
    field = create_simple_union_field()
    assert field.validate_and_build("123") == "123"  # Should be treated as string, not converted to int


def create_test_union_field():
    """Helper function to create a UnionField with string and number options."""
    return UnionField(
        name="test_union",
        description="Test union field",
        options=[
            partial(StringField, min_length=3),
            partial(NumericalField, value_type=int, min_value=0)
        ]
    )


def test_union_field_rejects_short_string():
    """Test that UnionField rejects strings that are too short for StringField."""
    field = create_test_union_field()
    with pytest.raises(ValidationError):
        field.validate_and_build("ab")


def test_union_field_rejects_negative_number():
    """Test that UnionField rejects numbers below the minimum value for NumericalField."""
    field = create_test_union_field()
    with pytest.raises(ValidationError, match="does not match any allowed type"):
        field.validate_and_build(-1)


def test_union_field_rejects_incompatible_type():
    """Test that UnionField rejects values of incompatible types."""
    field = create_test_union_field()
    with pytest.raises(ValidationError, match="does not match any allowed type"):
        field.validate_and_build([1, 2, 3])


def create_complex_union_field():
    """Helper function to create a UnionField with complex types."""
    return UnionField(
        name="complex_union",
        description="Union with complex types",
        options=[
            partial(ListField, item_field=partial(NumericalField, value_type=int)),
            partial(TupleField,
                    element_fields=[
                        partial(StringField, name="name", description="Name"),
                        partial(NumericalField, value_type=int, name="age", description="Age")
                    ])
        ]
    )


def create_collection_and_object_union_field():
    """Helper function to create a union with list, tuple, and object options."""
    return UnionField(
        name="mixed_complex_union",
        description="Union with list, tuple, and object options",
        options=[
            partial(ListField, item_field=partial(NumericalField, value_type=int)),
            partial(TupleField, element_fields=[partial(StringField, cast_to_string=False), partial(NumericalField, value_type=int)]),
            partial(ObjectField, factory=FIELD_FACTORY, class_path="tests.fields.composite.test_union_field.UnionPerson")
        ]
    )


def test_union_field_accepts_list_of_numbers():
    """Test that UnionField accepts a list of numbers when ListField is an option."""
    field = create_complex_union_field()
    assert field.validate_and_build([1, 2, 3]) == [1, 2, 3]


def test_union_field_accepts_tuple_of_mixed_types():
    """Test that UnionField accepts a tuple of mixed types when TupleField is an option."""
    field = create_complex_union_field()
    assert field.validate_and_build(("John", 30)) == ("John", 30)


def test_union_field_parses_string_representation_of_tuple():
    """Test that UnionField parses string representation of a tuple when TupleField is an option."""
    field = create_complex_union_field()
    assert field.validate_and_build("('Alice', 25)") == ("Alice", 25)


def test_union_field_accepts_list_tuple_and_object_consistently():
    """Union should route values to list/tuple/object options and preserve their validated output types."""
    field = create_collection_and_object_union_field()

    assert field.validate_and_build([1, 2, 3]) == [1, 2, 3]
    assert field.validate_and_build(("Alice", 25)) == ("Alice", 25)

    person = field.validate_and_build({"name": "Bob", "age": 31})
    assert isinstance(person, UnionPerson)
    assert person.name == "Bob"
    assert person.age == 31


def test_union_field_list_like_tuple_input_hits_limit():
    """A list value with tuple-like contents should not be accepted by the tuple option."""
    field = create_collection_and_object_union_field()

    with pytest.raises(ValidationError, match="does not match any allowed type"):
        field.validate_and_build(["Alice", 25])


def test_union_field_required_rejects_none():
    """Test that UnionField with required=True rejects None."""
    field = UnionField(
        name="test_required",
        description="Test required union",
        required=True,
        options=[partial(StringField)]
    )
    with pytest.raises(ValidationError):
        field.validate_and_build(None)


def test_union_field_optional_rejects_none_without_default():
    """Test that UnionField with required=False and no default rejects None."""
    field = UnionField(
        name="test_optional",
        description="Test optional union",
        required=False,
        default="",
        options=[partial(StringField)]
    )
    with pytest.raises(ValidationError):
        field.validate_and_build(None)


def test_union_field_error_messages():
    """Test that UnionField provides useful error messages."""
    field = UnionField(
        name="test_errors",
        description="Test error messages",
        options=[
            partial(StringField, min_length=3),
            partial(NumericalField, value_type=int, min_value=0)
        ]
    )

    with pytest.raises(ValidationError):
        field.validate_and_build(False)


def test_union_field_accepts_various_object_types_with_dynamic_object_option():
    """UnionField should validate and build different object types via dynamic ObjectField resolution."""
    field = UnionField(
        name="object_union",
        description="Union with dynamic object option",
        options=[
            partial(ObjectField, factory=FIELD_FACTORY),
        ]
    )

    person = field.validate_and_build(
        {"_type_": "tests.fields.composite.test_union_field.UnionPerson", "name": "Alice", "age": 30}
    )
    pet = field.validate_and_build(
        {"_type_": "tests.fields.composite.test_union_field.UnionPet", "kind": "cat"}
    )

    assert isinstance(person, UnionPerson)
    assert person.name == "Alice"
    assert person.age == 30
    assert isinstance(pet, UnionPet)
    assert pet.kind == "cat"


def test_union_field_accepts_object_deriving_from_base_class():
    """UnionField should accept derived object types when ObjectField is configured with a base class."""
    field = UnionField(
        name="animal_union",
        description="Union with base animal object",
        options=[
            partial(
                ObjectField,
                factory=FIELD_FACTORY,
                class_path="tests.fields.composite.test_union_field.BaseUnionAnimal"
            ),
        ]
    )

    dog = field.validate_and_build(
        {"_type_": "tests.fields.composite.test_union_field.UnionDog", "name": "Rex", "breed": "Labrador"}
    )
    cat = field.validate_and_build(
        {"_type_": "tests.fields.composite.test_union_field.UnionCat", "name": "Mittens", "lives": 7}
    )

    assert isinstance(dog, UnionDog)
    assert dog.name == "Rex"
    assert dog.breed == "Labrador"
    assert isinstance(cat, UnionCat)
    assert cat.name == "Mittens"
    assert cat.lives == 7


def test_union_field_rejects_non_subclass_for_base_class_object_option():
    """UnionField should reject object type that is not a subclass of configured base class."""
    field = UnionField(
        name="animal_union",
        description="Union with base animal object",
        options=[
            partial(
                ObjectField,
                factory=FIELD_FACTORY,
                class_path="tests.fields.composite.test_union_field.BaseUnionAnimal"
            ),
        ]
    )

    with pytest.raises(ValidationError, match="does not match any allowed type"):
        field.validate_and_build(
            {"_type_": "tests.fields.composite.test_union_field.UnionCar", "model": "Roadster"}
        )
