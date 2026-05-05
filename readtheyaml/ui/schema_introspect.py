from copy import deepcopy
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Union

from readtheyaml.fields.base.any_field import AnyField
from readtheyaml.fields.base.bool_field import BoolField
from readtheyaml.fields.base.enum_field import EnumField
from readtheyaml.fields.base.none_field import NoneField
from readtheyaml.fields.base.numerical_field import NumericalField
from readtheyaml.fields.base.object_field import ObjectField
from readtheyaml.fields.base.string_field import StringField
from readtheyaml.fields.composite.list_field import ListField
from readtheyaml.fields.composite.tuple_field import TupleField
from readtheyaml.fields.composite.union_field import UnionField
from readtheyaml.schema import Schema


@dataclass(frozen=True)
class FieldIntrospection:
    key: str
    type: str
    required: bool
    has_default: bool
    default: Any
    description: str
    constraints: Dict[str, Any]
    when: Optional[Dict[str, Any]]


@dataclass(frozen=True)
class SectionIntrospection:
    path: str
    name: str
    description: str
    required: bool
    has_default: bool
    default: Any
    when: Optional[Dict[str, Any]]
    fields: List[FieldIntrospection]
    subsections: List["SectionIntrospection"]


def introspect_schema(schema: Schema) -> SectionIntrospection:
    return _introspect_section(schema=schema, path=schema.name or "<root>")


def introspect_schema_dict(schema: Schema) -> Dict[str, Any]:
    return asdict(introspect_schema(schema))


def flatten_field_paths(section: Union[SectionIntrospection, Dict[str, Any]]) -> List[str]:
    if isinstance(section, dict):
        return _flatten_field_paths_from_dict(section)
    return _flatten_field_paths_from_dataclass(section)


def _introspect_section(schema: Schema, path: str) -> SectionIntrospection:
    fields = [
        _introspect_field(key, schema.fields[key])
        for key in schema.fields
    ]
    subsections = [
        _introspect_section(schema.subsections[key], _join_path(path, key))
        for key in schema.subsections
    ]
    return SectionIntrospection(
        path=path,
        name=schema.name or "",
        description=schema.description or "",
        required=schema.required,
        has_default=schema.has_default,
        default=deepcopy(schema.default) if schema.has_default else None,
        when=deepcopy(schema.when),
        fields=fields,
        subsections=subsections,
    )


def _introspect_field(key: str, field: Any) -> FieldIntrospection:
    has_default = (not field.required) and (field.raw_default is not None or field.default is not None)
    default_value = deepcopy(field.default) if has_default else None
    return FieldIntrospection(
        key=key,
        type=_field_type_string(field),
        required=field.required,
        has_default=has_default,
        default=default_value,
        description=field.description,
        constraints=_field_constraints(field),
        when=deepcopy(field.when),
    )


def _field_type_string(field: Any) -> str:
    if isinstance(field, NumericalField):
        return field.value_type.__name__
    if isinstance(field, StringField):
        return "str"
    if isinstance(field, BoolField):
        return "bool"
    if isinstance(field, EnumField):
        return "enum"
    if isinstance(field, NoneField):
        return "none"
    if isinstance(field, AnyField):
        return "any"
    if isinstance(field, ListField):
        return f"list({_field_type_string(field.item_field)})"
    if isinstance(field, TupleField):
        inner = ", ".join(_field_type_string(slot) for slot in field._slots)
        return f"tuple({inner})"
    if isinstance(field, UnionField):
        inner = " | ".join(_field_type_string(option) for option in field._options)
        return f"union({inner})"
    if isinstance(field, ObjectField):
        if field.class_path:
            return f"object({field.class_path})"
        return "object"
    return field.__class__.__name__


def _field_constraints(field: Any) -> Dict[str, Any]:
    constraints: Dict[str, Any] = {}
    if isinstance(field, NumericalField):
        if field.min_value is not None:
            constraints["min"] = field.min_value
        if field.max_value is not None:
            constraints["max"] = field.max_value
    elif isinstance(field, StringField):
        if field.min_length > 0:
            constraints["min_length"] = field.min_length
        if field.max_length != -1:
            constraints["max_length"] = field.max_length
    elif isinstance(field, EnumField):
        constraints["enum_values"] = list(field.choices)
    elif isinstance(field, ListField):
        if field.min_length is not None:
            constraints["min_length"] = field.min_length
        if field.max_length is not None:
            constraints["max_length"] = field.max_length
    return constraints


def _flatten_field_paths_from_dataclass(section: SectionIntrospection) -> List[str]:
    paths: List[str] = []
    for field in section.fields:
        paths.append(_join_path(section.path, field.key))
    for subsection in section.subsections:
        paths.extend(_flatten_field_paths_from_dataclass(subsection))
    return paths


def _flatten_field_paths_from_dict(section: Dict[str, Any]) -> List[str]:
    paths: List[str] = []
    for field in section.get("fields", []):
        paths.append(_join_path(section["path"], field["key"]))
    for subsection in section.get("subsections", []):
        paths.extend(_flatten_field_paths_from_dict(subsection))
    return paths


def _join_path(prefix: str, key: str) -> str:
    if not prefix:
        return key
    return f"{prefix}.{key}"
