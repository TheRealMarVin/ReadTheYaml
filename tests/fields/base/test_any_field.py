import pytest

from readtheyaml.exceptions.format_error import FormatError
from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.fields.base.any_field import AnyField
from readtheyaml.fields.field_factory import FIELD_FACTORY
from readtheyaml.schema import Schema


@pytest.mark.parametrize("type_name", ["any", "Any", "ANY"])
def test_factory_accepts_supported_any_type_names(type_name):
    field = FIELD_FACTORY.create_field(type_name, name="anything", description="accepts anything")
    assert isinstance(field, AnyField)


@pytest.mark.parametrize("type_name", ["aNy", "anything", "all", "object"])
def test_factory_rejects_unsupported_any_type_names(type_name):
    with pytest.raises(ValueError, match="Unknown field type"):
        FIELD_FACTORY.create_field(type_name, name="anything", description="accepts anything")


def test_any_field_from_type_string_rejects_non_any_type_names():
    assert AnyField.from_type_string("str", name="anything", factory=FIELD_FACTORY, description="desc") is None


@pytest.mark.parametrize("value", [None, True, False, 0, 42, -3.14, "", "hello", b"bytes", [1, "x", {"k": "v"}], (1, 2, 3), {"k": "v"}, {"nested": {"arr": [1, 2, 3], "obj": {"enabled": True}}}])
def test_any_field_accepts_all_common_value_shapes(value):
    field = AnyField(name="anything", description="accepts anything")
    assert field.validate_and_build(value) == value


def test_any_field_accepts_user_defined_objects():
    class Dummy:
        def __init__(self, value):
            self.value = value

    value = Dummy(10)
    field = AnyField(name="anything", description="accepts anything")

    assert field.validate_and_build(value) is value
    assert field.validate_and_build(value).value == 10


def test_any_field_optional_with_none_default():
    field = AnyField(name="anything", description="optional any", required=False, default=None)
    assert field.required is False
    assert field.default is None


def test_any_field_optional_without_default_rejected():
    with pytest.raises(FormatError, match="optional AnyField must define an explicit default value"):
        AnyField(name="anything", description="optional any", required=False)


@pytest.mark.parametrize("default", ["hello", 42, 3.14, {"nested": {"x": 1}}])
def test_any_field_optional_with_typed_defaults(default):
    field = AnyField(name="anything", description="optional any", required=False, default=default)
    assert field.default == default


def test_any_field_required_rejects_default():
    with pytest.raises(FormatError, match="default value for a required field"):
        AnyField(name="anything", description="required any", required=True, default="x")


def test_schema_optional_any_field_missing_uses_none_default():
    schema = Schema(
        name="root",
        fields={"anything": AnyField(name="anything", description="optional any", required=False, default=None)}
    )

    built, data_with_default = schema.build_and_validate({})
    assert built["anything"] is None
    assert data_with_default["anything"] is None


def test_schema_from_dict_optional_any_without_default_rejected():
    with pytest.raises(ValidationError, match="optional AnyField must define an explicit default value"):
        Schema._from_dict(
            {
                "payload": {
                    "type": "any",
                    "description": "Arbitrary payload",
                    "required": False,
                }
            }
        )


@pytest.mark.parametrize("default", ["hello", 42, 3.14, {"nested": {"x": 1}}])
def test_schema_optional_any_field_missing_uses_typed_defaults(default):
    schema = Schema(
        name="root",
        fields={"anything": AnyField(name="anything",description="optional any", required=False, default=default)}
    )

    built, data_with_default = schema.build_and_validate({})
    assert built["anything"] == default
    assert data_with_default["anything"] == default


def _build_single_any_schema(required=True, default=None, include_default=False):
    field_schema = {
        "type": "any",
        "description": "Arbitrary payload",
        "required": required,
    }
    if include_default:
        field_schema["default"] = default

    return Schema._from_dict({"payload": field_schema})


def test_schema_any_accepts_null_value():
    schema = _build_single_any_schema(required=True)
    built, data_with_default = schema.build_and_validate({"payload": None})

    assert built["payload"] is None
    assert data_with_default["payload"] is None


def test_schema_any_accepts_boolean_value():
    schema = _build_single_any_schema(required=True)
    built, data_with_default = schema.build_and_validate({"payload": True})

    assert built["payload"] is True
    assert data_with_default["payload"] is True


def test_schema_any_accepts_integer_value():
    schema = _build_single_any_schema(required=True)
    built, data_with_default = schema.build_and_validate({"payload": 42})

    assert built["payload"] == 42
    assert data_with_default["payload"] == 42


def test_schema_any_accepts_float_value():
    schema = _build_single_any_schema(required=True)
    built, data_with_default = schema.build_and_validate({"payload": 3.14})

    assert built["payload"] == 3.14
    assert data_with_default["payload"] == 3.14


def test_schema_any_accepts_string_value():
    schema = _build_single_any_schema(required=True)
    built, data_with_default = schema.build_and_validate({"payload": "hello"})

    assert built["payload"] == "hello"
    assert data_with_default["payload"] == "hello"


def test_schema_any_accepts_list_value():
    schema = _build_single_any_schema(required=True)
    payload = [1, "two", {"three": 3}]
    built, data_with_default = schema.build_and_validate({"payload": payload})

    assert built["payload"] == payload
    assert data_with_default["payload"] == payload


def test_schema_any_accepts_dict_value():
    schema = _build_single_any_schema(required=True)
    payload = {"feature": "on", "ratio": 0.7}
    built, data_with_default = schema.build_and_validate({"payload": payload})

    assert built["payload"] == payload
    assert data_with_default["payload"] == payload


def test_schema_any_optional_uses_default_when_missing():
    schema = _build_single_any_schema(required=False, default={"mode": "safe"}, include_default=True)
    built, data_with_default = schema.build_and_validate({})

    assert built["payload"] == {"mode": "safe"}
    assert data_with_default["payload"] == {"mode": "safe"}


def test_schema_any_required_missing_field_raises():
    schema = _build_single_any_schema(required=True)

    with pytest.raises(ValidationError, match="Missing required field 'payload'"):
        schema.build_and_validate({})


def test_schema_any_from_yaml_accepts_string_config_value(tmp_path):
    schema_path = tmp_path / "schema.yaml"
    config_path = tmp_path / "config.yaml"

    schema_path.write_text(
        """
payload:
  type: any
  description: Arbitrary payload
""".strip(),
        encoding="utf-8",
    )
    config_path.write_text(
        """
payload: from-yaml
""".strip(),
        encoding="utf-8",
    )

    schema = Schema.from_yaml(str(schema_path))
    built, data_with_default = schema.validate_file(config_path)

    assert built["payload"] == "from-yaml"
    assert data_with_default["payload"] == "from-yaml"


def test_schema_any_from_yaml_accepts_object_config_value(tmp_path):
    schema_path = tmp_path / "schema.yaml"
    config_path = tmp_path / "config.yaml"

    schema_path.write_text(
        """
payload:
  type: any
  description: Arbitrary payload
""".strip(),
        encoding="utf-8",
    )
    config_path.write_text(
        """
payload:
  a: 1
  b:
    - true
    - text
""".strip(),
        encoding="utf-8",
    )

    schema = Schema.from_yaml(str(schema_path))
    built, data_with_default = schema.validate_file(config_path)

    assert built["payload"]["a"] == 1
    assert built["payload"]["b"] == [True, "text"]
    assert data_with_default["payload"]["b"] == [True, "text"]


def test_schema_any_mutable_default_is_isolated_between_validations():
    schema = Schema._from_dict(
        {
            "payload": {
                "type": "any",
                "description": "Arbitrary payload",
                "required": False,
                "default": {"items": []},
            }
        }
    )

    built_first, _ = schema.build_and_validate({})
    built_first["payload"]["items"].append("x")

    built_second, data_with_default_second = schema.build_and_validate({})
    assert built_second["payload"]["items"] == []
    assert data_with_default_second["payload"]["items"] == []
