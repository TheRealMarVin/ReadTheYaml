import re
from functools import partial
from typing import Optional

from readtheyaml.fields.bool_field import BoolField
from readtheyaml.fields.field import Field
from readtheyaml.fields.list_field import ListField
from readtheyaml.fields.numerical_field import NumericalField
from readtheyaml.fields.string_field import StringField

FIELD_REGISTRY = {
    "int": partial(NumericalField, int),
    "float": partial(NumericalField, float),
    "str": StringField,
    "bool": BoolField,
    # We handle 'list(...)' dynamically
}

def build_field(definition: dict, name: str) -> Field:
    constructor = parse_field_type(definition["type"])
    field = constructor(name=name, **definition)

    return field


def parse_field_type(type_str: str) -> Field:
    list_match = re.fullmatch(r"list\((.+)\)", type_str)
    if list_match:
        item_type_str = list_match.group(1)
        item_field = parse_field_type(item_type_str)
        return ListField(item_field=item_field)

    constructor = FIELD_REGISTRY.get(type_str)
    if not constructor:
        raise ValueError(f"Unknown field type: {type_str}")
    return constructor
