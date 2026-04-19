import pytest

from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.schema import Schema


class UnionCfgEntity:
    def __init__(self, name: str):
        self.name = name


class UnionCfgPerson(UnionCfgEntity):
    def __init__(self, name: str, age: int):
        super().__init__(name)
        self.name = name
        self.age = age


class UnionCfgPet(UnionCfgEntity):
    def __init__(self, name: str, kind: str):
        super().__init__(name)
        self.kind = kind


class UnionCfgCar(UnionCfgEntity):
    def __init__(self, name: str, model: str):
        super().__init__(name)
        self.model = model


def _entity_class_path() -> str:
    return "tests.schemas.composite.test_union_field_file_configs.UnionCfgEntity"


def _person_class_path() -> str:
    return "tests.schemas.composite.test_union_field_file_configs.UnionCfgPerson"


def _pet_class_path() -> str:
    return "tests.schemas.composite.test_union_field_file_configs.UnionCfgPet"


def _car_class_path() -> str:
    return "tests.schemas.composite.test_union_field_file_configs.UnionCfgCar"


def _required_union_schema_yaml(type_literal: str = "union[int, str]") -> str:
    return f"""
        value:
          type: {type_literal}
          description: Int or string value
          required: true
    """


def _optional_union_schema_yaml(type_literal: str, default_literal: str) -> str:
    return f"""
        value:
          type: {type_literal}
          description: Union value
          required: false
          default: {default_literal}
    """


def test_union_required_accepts_int(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _required_union_schema_yaml(), "config.yaml": "value: 42"}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["value"] == 42
    assert data_with_default["value"] == 42


def test_union_required_accepts_string(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _required_union_schema_yaml(), "config.yaml": 'value: "alpha"'}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["value"] == "alpha"
    assert data_with_default["value"] == "alpha"


def test_union_required_missing_field_rejected(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _required_union_schema_yaml(), "config.yaml": "{}"}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    with pytest.raises(ValidationError, match="Missing required field 'value'"):
        schema.validate_file(files["config.yaml"])


def test_union_required_rejects_unmatched_value(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _required_union_schema_yaml("union[int, bool]"), "config.yaml": "value: []"}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    with pytest.raises(ValidationError, match="does not match any allowed type"):
        schema.validate_file(files["config.yaml"])


def test_union_required_accepts_bool_when_configured(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _required_union_schema_yaml("union[int, bool]"), "config.yaml": "value: true"}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["value"] is True
    assert data_with_default["value"] is True


def test_union_pipe_syntax_supported(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _required_union_schema_yaml("int | str"), "config.yaml": "value: 7"}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, _ = schema.validate_file(files["config.yaml"])

    assert built["value"] == 7


def test_union_pipe_syntax_supported_for_string(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _required_union_schema_yaml("int | str"), "config.yaml": 'value: "beta"'}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, _ = schema.validate_file(files["config.yaml"])

    assert built["value"] == "beta"


def test_union_option_order_prefers_first_matching_type(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _required_union_schema_yaml("str | int"), "config.yaml": 'value: "123"'}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    # String option is first, so this remains string instead of int coercion.
    assert built["value"] == "123"
    assert data_with_default["value"] == "123"


def test_union_optional_missing_field_uses_default(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _optional_union_schema_yaml("union[int, str]", '"seed"'), "config.yaml": "{}"}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["value"] == "seed"
    assert data_with_default["value"] == "seed"


def test_union_optional_provided_value_overrides_default(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _optional_union_schema_yaml("union[int, str]", "5"), "config.yaml": 'value: "live"'}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["value"] == "live"
    assert data_with_default["value"] == "live"


def test_union_optional_provided_int_overrides_default(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _optional_union_schema_yaml("union[int, str]", '"seed"'), "config.yaml": "value: 9"}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["value"] == 9
    assert data_with_default["value"] == 9


def test_union_optional_without_default_rejected(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": """
                value:
                  type: union[int, str]
                  description: Union value
                  required: false
            """,
            "config.yaml": "{}",
        }
    )

    with pytest.raises(ValidationError, match="invalid default value"):
        Schema.from_yaml(str(files["schema.yaml"]))


def test_union_with_none_allows_null_value(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _required_union_schema_yaml("union[int, None]"), "config.yaml": "value: null"}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["value"] is None
    assert data_with_default["value"] is None


def test_union_with_none_allows_non_none_value(create_schema_examples):
    files = create_schema_examples(
        {"schema.yaml": _required_union_schema_yaml("union[int, None]"), "config.yaml": "value: 11"}
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert built["value"] == 11
    assert data_with_default["value"] == 11


def test_union_with_more_than_two_members_accepts_all_members(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": _required_union_schema_yaml("union[int, str, bool]"),
            "int.yaml": "value: 5",
            "str.yaml": 'value: "delta"',
            "bool.yaml": "value: true",
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))

    built_int, _ = schema.validate_file(files["int.yaml"])
    built_str, _ = schema.validate_file(files["str.yaml"])
    built_bool, _ = schema.validate_file(files["bool.yaml"])

    assert built_int["value"] == 5
    assert built_str["value"] == "delta"
    assert built_bool["value"] is True


def test_union_object_and_none_with_dynamic_object_type(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": _required_union_schema_yaml(f"union[object[{_entity_class_path()}], None]"),
            "person.yaml": f"""
                value:
                  _type_: {_person_class_path()}
                  name: Alice
                  age: 30
            """,
            "pet.yaml": f"""
                value:
                  _type_: {_pet_class_path()}
                  name: Luna
                  kind: cat
            """,
            "car.yaml": f"""
                value:
                  _type_: {_car_class_path()}
                  name: Comet
                  model: Roadster
            """,
            "none.yaml": "value: null",
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))

    built_person, _ = schema.validate_file(files["person.yaml"])
    assert isinstance(built_person["value"], UnionCfgPerson)
    assert built_person["value"].name == "Alice"
    assert built_person["value"].age == 30

    built_pet, _ = schema.validate_file(files["pet.yaml"])
    assert isinstance(built_pet["value"], UnionCfgPet)
    assert built_pet["value"].name == "Luna"
    assert built_pet["value"].kind == "cat"

    built_car, _ = schema.validate_file(files["car.yaml"])
    assert isinstance(built_car["value"], UnionCfgCar)
    assert built_car["value"].name == "Comet"
    assert built_car["value"].model == "Roadster"

    built_none, data_none = schema.validate_file(files["none.yaml"])
    assert built_none["value"] is None
    assert data_none["value"] is None


def test_union_fixed_object_and_none(create_schema_examples):
    files = create_schema_examples(
        {
            "schema.yaml": _required_union_schema_yaml(f"union[object[{_person_class_path()}], None]"),
            "config.yaml": """
                value:
                  name: Bob
                  age: 31
            """,
        }
    )

    schema = Schema.from_yaml(str(files["schema.yaml"]))
    built, data_with_default = schema.validate_file(files["config.yaml"])

    assert isinstance(built["value"], UnionCfgPerson)
    assert built["value"].name == "Bob"
    assert built["value"].age == 31
    assert data_with_default["value"] == {"name": "Bob", "age": 31}

    files_none = create_schema_examples(
        {
            "schema.yaml": _required_union_schema_yaml(f"union[object[{_person_class_path()}], None]"),
            "config.yaml": "value: null",
        }
    )
    schema_none = Schema.from_yaml(str(files_none["schema.yaml"]))
    built_none, data_none = schema_none.validate_file(files_none["config.yaml"])
    assert built_none["value"] is None
    assert data_none["value"] is None
