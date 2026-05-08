from copy import deepcopy
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

from readtheyaml.schema import Schema
from readtheyaml.ui.constants import ROOT_PATH
from readtheyaml.ui.form_helpers import join_path


@dataclass(frozen=True)
class FieldIntrospection:
    key: str
    field_type: str
    widget_type: Any
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


def introspect_schema_dict(schema: Schema):
    section = _introspect_section(schema=schema, path=schema.name or ROOT_PATH)
    return asdict(section)


def _introspect_section(schema: Schema, path: str):
    fields = [_introspect_field(key, schema.fields[key]) for key in schema.fields]
    subsections = [_introspect_section(schema.subsections[key], join_path(path, key)) for key in schema.subsections]

    return SectionIntrospection(
        path=path,
        name=schema.name or "",
        description=schema.description or "",
        required=schema.required,
        has_default=schema.has_default,
        default=deepcopy(schema.default) if schema.has_default else None,
        when=deepcopy(schema.when),
        fields=fields,
        subsections=subsections
    )


def _introspect_field(key: str, field: Any):
    has_default = (not field.required) and (field.raw_default is not None or field.default is not None)
    default_value = deepcopy(field.default) if has_default else None
    constraints = deepcopy(field.constraint_specs())
    if field.field_type() == "str" and constraints.get("length_unit") == "characters":
        constraints.pop("length_unit", None)
    return FieldIntrospection(
        key=key,
        field_type=field.field_type(),
        widget_type=field.ui_widget_type(),
        required=field.required,
        has_default=has_default,
        default=default_value,
        description=field.description,
        constraints=constraints,
        when=deepcopy(field.when)
    )


