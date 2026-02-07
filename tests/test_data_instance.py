import pytest
import yaml

from readtheyaml.data_instance import DataInstance
from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.schema import Schema


def test_basic_data_instance_build_and_access():
    """Test basic creation and access of built values with no defaults."""
    schema_dict = {
        "username": {
            "type": "str",
            "description": "The user's name"
        },
        "age": {
            "type": "int",
            "description": "The user's age"
        }
    }
    schema = Schema._from_dict(schema_dict)
    data = {"username": "Alice", "age": 30}

    instance = DataInstance(data, schema)

    assert instance["username"] == "Alice"
    assert instance["age"] == 30
    assert instance.built == data
    assert instance.data_with_default == data


def test_data_instance_strict_mode_rejects_unknown_key():
    """Test that unknown keys raise ValidationError in strict mode."""
    schema_dict = {
        "x": {
            "type": "int",
            "description": "some int"
        }
    }
    schema = Schema._from_dict(schema_dict)
    data = {"x": 1, "y": 2}

    with pytest.raises(ValidationError, match="Unexpected key"):
        DataInstance(data, schema, strict=True)


def test_data_instance_non_strict_allows_extra_fields():
    """Test that extra fields are preserved when strict=False."""
    schema_dict = {
        "x": {
            "type": "int",
            "description": "some int"
        }
    }
    schema = Schema._from_dict(schema_dict)
    data = {"x": 1, "y": 2}

    instance = DataInstance(data, schema, strict=False)
    assert instance["x"] == 1
    assert instance.built["y"] == 2  # extra field preserved


def test_data_instance_dump_without_defaults():
    """Test that dump output matches input if no defaults are used."""
    schema_dict = {
        "foo": {
            "type": "str",
            "description": "some string"
        }
    }
    schema = Schema._from_dict(schema_dict)
    data = {"foo": "bar"}

    instance = DataInstance(data, schema)
    dumped = yaml.safe_dump(instance.data_with_default)

    assert yaml.safe_load(dumped) == data


def test_data_instance_dump_with_defaults():
    """Test that default values are added, included in the dump, and still schema-valid."""
    schema_dict = {
        "foo": {
            "type": "str",
            "default": "bar",
            "required": False,
            "description": "optional string"
        },
        "x": {
            "type": "int",
            "description": "required int"
        }
    }
    schema = Schema._from_dict(schema_dict)
    data = {"x": 123}

    instance = DataInstance(data, schema)
    dumped = yaml.safe_dump(instance.data_with_default)
    dumped_data = yaml.safe_load(dumped)

    assert dumped_data["x"] == 123
    assert dumped_data["foo"] == "bar"
    assert instance["foo"] == "bar"

    # New: validate the dumped result against the schema
    schema.build_and_validate(dumped_data, strict=True)

def test_data_instance_getitem_empty_key_raises():
    """Test that accessing an empty key raises a KeyError."""
    schema_dict = {
        "a": {
            "type": "int",
            "description": "some int"
        }
    }
    schema = Schema._from_dict(schema_dict)
    data = {"a": 42}

    instance = DataInstance(data, schema)

    with pytest.raises(KeyError, match="Empty key"):
        _ = instance[""]


def test_data_instance_nested_access():
    """Test that dotted key access works for nested subsections with defaults."""
    schema_dict = {
        "db": {  # Not a field — this is a subsection
            "description": "database settings",
            "required": True,
            "host": {
                "type": "str",
                "description": "database host"
            },
            "port": {
                "type": "int",
                "default": 5432,
                "required": False,
                "description": "database port"
            }
        }
    }
    schema = Schema._from_dict(schema_dict)
    data = {"db": {"host": "localhost"}}

    instance = DataInstance(data, schema)

    assert instance["db.host"] == "localhost"
    assert instance["db.port"] == 5432

def test_data_instance_nested_access_with_dict_style():
    """Test that nested access works using chained dictionary-style indexing."""
    schema_dict = {
        "db": {
            "description": "database settings",
            "required": True,
            "host": {
                "type": "str",
                "description": "database host"
            },
            "port": {
                "type": "int",
                "default": 5432,
                "required": False,
                "description": "database port"
            }
        }
    }
    schema = Schema._from_dict(schema_dict)
    data = {"db": {"host": "localhost"}}

    instance = DataInstance(data, schema)

    db_section = instance["db"]
    assert isinstance(db_section, dict)  # assuming build() returns nested dicts

    assert db_section["host"] == "localhost"
    assert db_section["port"] == 5432

def test_data_instance_dump_is_yaml_serializable():
    """Test that DataInstance.dump() produces valid YAML output."""
    schema_dict = {
        "val": {
            "type": "int",
            "default": 42,
            "required": False,
            "description": "some int"
        }
    }
    schema = Schema._from_dict(schema_dict)
    data = {}

    instance = DataInstance(data, schema)

    # This should never raise
    parsed = yaml.safe_load(yaml.safe_dump(instance.data_with_default))
    assert parsed == {"val": 42}

def test_data_instance_dotted_access_fails_on_non_dict():
    """Test that dotted access fails if intermediate value is not a dict."""
    schema_dict = {
        "config": {
            "type": "str",
            "description": "string value, not a dict"
        }
    }
    schema = Schema._from_dict(schema_dict)
    data = {"config": "just_a_string"}

    instance = DataInstance(data, schema)

    with pytest.raises(TypeError):
        _ = instance["config.subkey"]

