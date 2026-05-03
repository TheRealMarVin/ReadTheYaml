import inspect
from enum import Enum
from typing import Any

from readtheyaml.fields.field import Field

def get_reserved_keywords_by_loaded_fields():
    reserved_by_class = {}
    allowed_field_names = {"when"}

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
            reserved_by_class[cls.__name__] = keywords - allowed_field_names

    return reserved_by_class


def normalize_for_doc_dump(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {k: normalize_for_doc_dump(v) for k, v in value.items()}
    if isinstance(value, list):
        return [normalize_for_doc_dump(v) for v in value]
    if isinstance(value, tuple):
        return tuple(normalize_for_doc_dump(v) for v in value)
    return value
