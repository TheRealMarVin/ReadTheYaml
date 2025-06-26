import inspect
import types
import typing


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
