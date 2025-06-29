import importlib
import inspect
import re
import types
import typing

from readtheyaml.exceptions.validation_error import ValidationError


def get_params_and_defaults(target_class):
    sig = inspect.signature(target_class.__init__)
    hints = typing.get_type_hints(target_class.__init__)

    result = {}
    for name, param in sig.parameters.items():
        if name == "self":
            continue

        has_hint = name in hints
        hint = hints[name] if has_hint else None
        has_default = param.default is not inspect.Parameter.empty
        default = param.default if has_default else None

        result[name] = {
            "has_hint": has_hint,
            "hint": hint,
            "has_default": has_default,
            "default": default,
        }

    return result

def type_to_string(type_) -> str:
    if type_ is type(None):
        return "None"

    origin = typing.get_origin(type_)
    args = typing.get_args(type_)

    if origin in (typing.Union, types.UnionType):
        return " | ".join(type_to_string(arg) for arg in args)

    if origin is not None:
        name = origin.__name__ if hasattr(origin, "__name__") else str(origin)
        return f"{name}[{', '.join(type_to_string(arg) for arg in args)}]"

    # Handle simple types
    if hasattr(type_, "__module__") and hasattr(type_, "__name__"):
        if type_.__module__ == "builtins":
            return type_.__name__
        return f"object[{type_.__module__}.{type_.__name__}]"

    # Fallback for weird cases
    return repr(type_)

def import_type(dotted_path):
    module_path, _, class_name = dotted_path.rpartition(".")
    if not module_path:
        raise ValidationError(f"Invalid class path '{dotted_path}': missing module")
    try:
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
    except (ImportError, AttributeError) as e:
        raise ValidationError(f"Failed to import '{dotted_path}': {e}")

def _extract_types_for_composite(type_str: str, type_name: str) -> str | None:
    match = re.fullmatch(rf"{re.escape(type_name)}([\[\(])(.*)([\]\)])", type_str)
    if not match:
        return None

    opening, inner, closing = match.groups()
    if (opening == "[" and closing != "]") or (opening == "(" and closing != ")"):
        raise ValueError(f"Mismatched brackets in type: {type_str}")

    return inner

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