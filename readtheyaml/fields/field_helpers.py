import inspect
import re
from functools import partial

import yaml

from readtheyaml.fields.composite_field import CompositeField
from readtheyaml.fields.field import Field
from readtheyaml.fields.field_registery import FIELD_REGISTRY
from readtheyaml.fields.list_field import ListField
from readtheyaml.fields.object_field import ObjectField
from readtheyaml.fields.union_field import UnionField
from readtheyaml.fields.tuple_field import TupleField

def build_field(definition: dict, name: str, base_schema_dir: str) -> Field:
    if "$ref" in definition:
        ref_path = base_schema_dir / definition["$ref"]
        with open(ref_path) as f:
            ref_data = yaml.safe_load(f)
        definition = {**ref_data, **{k: v for k, v in definition.items() if k != "$ref"}}

    if "type" in definition:
        return build_terminal_field(definition, name)

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
    constructor = _parse_field_type(definition["type"])
    field = constructor(name=name, **definition)
    return field

def get_reserved_keywords_by_loaded_fields():
    reserved_by_class = {}

    for cls in Field.__subclasses__():
        keywords = set()

        # Traverse the method resolution order (MRO)
        for base in inspect.getmro(cls):
            if not issubclass(base, Field):
                break  # don't go past the base Field class

            try:
                sig = inspect.signature(base.__init__)
                params = set(sig.parameters) - {"self", "args", "kwargs"}
                keywords.update(params)
            except (ValueError, TypeError):
                continue

        if keywords:
            reserved_by_class[cls.__name__] = keywords

    return reserved_by_class

def _extract_types_for_composite(type_str: str, type_name: str) -> str | None:
    match = re.fullmatch(rf"{re.escape(type_name)}([\[\(])(.+)([\]\)])", type_str)
    if not match:
        return None  # Not a match at all

    opening, inner, closing = match.groups()
    if (opening == "[" and closing != "]") or (opening == "(" and closing != ")"):
        raise ValueError(f"Mismatched brackets in type: {type_str}")

    return inner

def _parse_field_type(type_str: str) -> Field:
    type_str = type_str.strip()

    object_inner = _extract_types_for_composite(type_str=type_str, type_name="object")
    if object_inner:
        return partial(ObjectField, element_fields=object_inner)

    tuple_inner = _extract_types_for_composite(type_str=type_str, type_name="tuple")
    if tuple_inner:
        element_specs = _split_top_level(tuple_inner, ',')
        element_fields = []
        for spec in element_specs:
            constructor = _parse_field_type(spec)
            if constructor is None:
                raise ValueError(f"Unknown element type in tuple: {spec}")
            element_fields.append(constructor)
        return partial(TupleField, element_fields=element_fields)

    list_inner = _extract_types_for_composite(type_str=type_str, type_name="list")
    if list_inner:
        constructor = _parse_field_type(list_inner)
        if constructor is None:
            raise ValueError(f"Unknown item type in list: {list_inner}")
        return partial(ListField, item_field=constructor)

    if '|' in type_str:
        parts = _split_top_level(type_str, '|')
        parsed_fields = []
        for part in parts:
            constructor = _parse_field_type(part)
            if constructor is None:
                raise ValueError(f"Unknown field type in union: {part}")
            parsed_fields.append(constructor)
        return partial(UnionField, options=parsed_fields)

    union_inner = _extract_types_for_composite(type_str=type_str, type_name="union")
    if union_inner:
        parts = _split_top_level(union_inner, ',')
        parsed_fields = []
        for part in parts:
            constructor = _parse_field_type(part)
            if constructor is None:
                raise ValueError(f"Unknown field type in union: {part}")
            parsed_fields.append(constructor)
        return partial(UnionField, options=parsed_fields)

    constructor = FIELD_REGISTRY.get(type_str)
    if not constructor:
        raise ValueError(f"Unknown field type: {type_str}")
    return constructor


def _split_top_level(s: str, sep: str) -> list[str]:
    parts, depth, last = [], 0, 0
    for i, ch in enumerate(s):
        if ch in "([":   depth += 1
        elif ch in ")]": depth -= 1
        elif ch == sep and depth == 0:
            parts.append(s[last:i].strip())
            last = i + 1
    parts.append(s[last:].strip())
    return parts
