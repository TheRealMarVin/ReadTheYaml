import inspect
import re
from functools import partial

from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.fields.field import Field
from readtheyaml.fields.field_registery import FIELD_REGISTRY
from readtheyaml.fields.composite.list_field import ListField
from readtheyaml.fields.base.object_field import ObjectField
from readtheyaml.fields.composite.union_field import UnionField
from readtheyaml.fields.composite.tuple_field import TupleField
from readtheyaml.utils.type_utils import import_type


def build_field(definition: dict, name: str, base_schema_dir: str) -> Field:
    if "type" not in definition:
        raise ValueError(f"Field with no type: {name}")

    current_type = definition["type"]
    constructor = _parse_field_type(current_type)
    field = constructor(name=name, **definition)
    return field

def get_reserved_keywords_by_loaded_fields():
    reserved_by_class = {}

    for cls in Field.__subclasses__():
        keywords = set()

        for base in inspect.getmro(cls):
            if not issubclass(base, Field):
                break

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
    match = re.fullmatch(rf"{re.escape(type_name)}([\[\(])(.*)([\]\)])", type_str)
    if not match:
        return None  # Not a match at all

    opening, inner, closing = match.groups()
    if (opening == "[" and closing != "]") or (opening == "(" and closing != ")"):
        raise ValueError(f"Mismatched brackets in type: {type_str}")

    return inner


def _parse_field_type(type_str: str) -> Field:
    type_str = type_str.strip()

    if len(type_str) == 0:
        raise ValueError(f"Unknown field type: Empty")

    object_inner = _extract_types_for_composite(type_str=type_str, type_name="object")
    if object_inner is not None:
        # For object[type] syntax, use the inner type as class_path
        return partial(ObjectField, factory=_parse_field_type, class_path=object_inner)

    tuple_inner = _extract_types_for_composite(type_str=type_str, type_name="tuple")
    if tuple_inner is not None:
        element_specs = _split_top_level(tuple_inner, ',')
        element_fields = []
        for spec in element_specs:
            constructor = _parse_field_type(spec)
            element_fields.append(constructor)
        return partial(TupleField, element_fields=element_fields)

    list_inner = _extract_types_for_composite(type_str=type_str, type_name="list")
    if list_inner is not None:
        constructor = _parse_field_type(list_inner)
        return partial(ListField, item_field=constructor)

    if '|' in type_str:
        parts = _split_top_level(type_str, '|')
        parsed_fields = []
        for part in parts:
            constructor = _parse_field_type(part)
            parsed_fields.append(constructor)
        return partial(UnionField, options=parsed_fields)

    union_inner = _extract_types_for_composite(type_str=type_str, type_name="union")
    if union_inner:
        parts = _split_top_level(union_inner, ',')
        parsed_fields = []
        for part in parts:
            constructor = _parse_field_type(part)
            parsed_fields.append(constructor)
        return partial(UnionField, options=parsed_fields)

    constructor = FIELD_REGISTRY.get(type_str)

    if not constructor:
        try:
            import_type(type_str)
            constructor = partial(ObjectField, factory=_parse_field_type, class_path=type_str)
        except ValidationError:
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
