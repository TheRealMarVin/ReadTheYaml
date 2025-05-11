import re
from functools import partial

import yaml

from readtheyaml.fields.composite_field import CompositeField
from readtheyaml.fields.field import Field
from readtheyaml.fields.field_registery import FIELD_REGISTRY
from readtheyaml.fields.list_field import ListField


def build_field(definition: dict, name: str, base_schema_dir: str) -> Field:
    if "$ref" in definition:
        # Load referenced field
        ref_path = base_schema_dir / definition["$ref"]
        with open(ref_path) as f:
            ref_data = yaml.safe_load(f)
        definition = {**ref_data, **{k: v for k, v in definition.items() if k != "$ref"}}

        # Terminal field
    if "type" in definition:
        return build_terminal_field(definition, name)

        # Composite field
    return CompositeField(
        name=name,
        required=definition.get("required", True),
        description=definition.get("description", ""),
        fields={
            key: build_field(key, val, base_schema_dir)
            for key, val in definition.items()
            if key not in {"required", "description"}
        }
    )

def build_terminal_field(definition: dict, name: str):
    constructor = parse_field_type(definition["type"])
    field = constructor(name=name, **definition)

    return field

def parse_field_type(type_str: str) -> Field:
    list_match = re.fullmatch(r"list\((.+)\)", type_str)
    if list_match:
        item_type_str = list_match.group(1)
        item_field = parse_field_type(item_type_str)
        return partial(ListField, item_field=item_field)

    constructor = FIELD_REGISTRY.get(type_str)
    if not constructor:
        raise ValueError(f"Unknown field type: {type_str}")
    return constructor
