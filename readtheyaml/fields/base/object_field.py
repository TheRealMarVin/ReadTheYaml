import inspect
from functools import partial

from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.fields.base.any_field import AnyField
from readtheyaml.fields.field import Field
from readtheyaml.utils.type_utils import type_to_string, get_params_and_defaults, import_type, \
    extract_types_for_composite


class ObjectField(Field):
    _sentinel = "_type_"  # key in config used to specify class name if not fixed

    def __init__(self, factory, class_path=None, **kwargs):
        super().__init__(**kwargs)
        self.class_path = class_path
        self.factory = factory
        self.subfields = {}
        self._fixed_class = None
        self._subfields_cache = {}

        if class_path:
            cls = import_type(class_path)
            self._fixed_class = cls
            self.subfields = self._build_subfields_from_type_hints(cls)
            self._subfields_cache[cls] = self.subfields

    def _build_subfields_from_type_hints(self, cls):
        subfields = {}
        try:
            hints = get_params_and_defaults(cls)
        except Exception:
            hints = {}

        for name, values in hints.items():
            if name == "self":
                continue
            try:
                if not values["has_hint"]:
                    field_builder = partial(AnyField)
                else:
                    type_as_string = type_to_string(values["hint"])
                    field_builder = partial(self.factory.create_field, type_str=type_as_string)

                subfields[name] = field_builder(name=name, description=name, required=not values["has_default"], default=values["default"])

            except Exception as e:
                print(e)  # fallback: skip unsupported
        return subfields

    def _get_subfields_for_class(self, cls):
        if cls not in self._subfields_cache:
            self._subfields_cache[cls] = self._build_subfields_from_type_hints(cls)
        return self._subfields_cache[cls]

    def validate_and_build(self, value):
        if not isinstance(value, dict):
            if self.class_path:
                try:
                    cls = self._fixed_class or import_type(self.class_path)
                    return cls(value)
                except Exception as e:
                    raise ValidationError(f"Field '{self.name}': Failed to create '{self.class_path}': {e}") from e
            raise ValidationError(f"Field '{self.name}': Expected a dictionary to instantiate object")

        cls = self._resolve_class(value)
        subfields = self._get_subfields_for_class(cls)

        extras = set(value) - self._get_constructor_params(cls) - {self._sentinel}
        if extras and not self._accepts_kwargs(cls):
            raise ValidationError(f"Field '{self.name}': Unexpected keys: {sorted(extras)}")

        # Validate type hints
        for param, field in subfields.items():
            if param in value:
                try:
                    field.validate_and_build(value[param])
                except ValidationError as e:
                    raise ValidationError(f"Field '{self.name}.{param}': {e}") from e

        try:
            return cls(**self._clear_sentinel(value))
        except Exception as e:
            raise ValidationError(f"Field '{self.name}': Failed to create '{cls.__name__}': {e}") from e

    def _resolve_class(self, mapping):
        if self.class_path:
            base_cls = self._fixed_class or import_type(self.class_path)
            if self._sentinel not in mapping:
                return base_cls

            resolved_cls = import_type(mapping[self._sentinel])
            if not isinstance(resolved_cls, type) or not issubclass(resolved_cls, base_cls):
                raise ValidationError(f"Field '{self.name}': '{mapping[self._sentinel]}' is not a subclass of '{self.class_path}'")
            return resolved_cls
        if self._sentinel not in mapping:
            raise ValidationError(f"Field '{self.name}': Missing '{self._sentinel}' key to resolve object type")
        return import_type(mapping[self._sentinel])

    def _clear_sentinel(self, mapping):
        return {k: v for k, v in mapping.items() if k != self._sentinel}

    def _get_constructor_params(self, cls):
        try:
            sig = inspect.signature(cls.__init__)
            return {p.name for p in sig.parameters.values() if p.name != "self"}
        except Exception:
            return set()

    def _accepts_kwargs(self, cls):
        try:
            sig = inspect.signature(cls.__init__)
            return any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
        except Exception:
            return False

    @staticmethod
    def from_type_string(type_str: str, name: str, factory, **kwargs) -> "Field":
        object_type = extract_types_for_composite(type_str=type_str, type_name="object")
        if object_type is not None:
            return ObjectField(name=name, factory=factory, class_path=object_type, **kwargs)
        else:
            try:
                import_type(type_str)
                return ObjectField(name=name, factory=factory, class_path=type_str, **kwargs)
            except ValidationError:
                pass # ok to do nothing

        return None
