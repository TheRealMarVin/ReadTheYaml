import importlib
import inspect

from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.fields.field import Field


class ObjectField(Field):
    _sentinel = "_type_"  # key in config used to specify class name if not fixed

    def __init__(self, class_path=None, **kwargs):
        super().__init__(**kwargs)
        self.class_path = class_path

    def validate(self, value):
        if not isinstance(value, dict):
            raise ValidationError("Field '{self.name}': Expected a dictionary to instantiate object")

        cls = self._resolve_class(value)
        sig = inspect.signature(cls.__init__)

        required = {
            p.name for p in sig.parameters.values()
            if p.name != "self" and p.default is inspect._empty
        }

        missing = required - value.keys()
        if missing:
            raise ValidationError(f"Field '{self.name}': Missing required keys: {sorted(missing)}")

        extras = set(value) - required - {self._sentinel}
        if extras and not self.meta.get("allow_extra", False):
            raise ValidationError(f"Field '{self.name}': Unexpected keys: {sorted(extras)}")

        try:
            result = cls(**self._clear_sentinel(value))
        except Exception as e:
            raise ValidationError(f"Field '{self.name}': Failed to create '{cls.__name__}': {e}")

        return result

    def _resolve_class(self, mapping):
        if self.class_path:
            return self._import(self.class_path)
        if self._sentinel not in mapping:
            raise ValidationError(f"Field '{self.name}': Missing '{self._sentinel}' key to resolve object type")
        return self._import(mapping[self._sentinel])

    def _import(self, dotted_path):
        module_path, _, class_name = dotted_path.rpartition(".")
        if not module_path:
            raise ValidationError(f"Field '{self.name}': Invalid class path '{dotted_path}': missing module")
        try:
            module = importlib.import_module(module_path)
            return getattr(module, class_name)
        except (ImportError, AttributeError) as e:
            raise ValidationError(f"Field '{self.name}': Failed to import '{dotted_path}': {e}")

    def _clear_sentinel(self, mapping):
        return {k: v for k, v in mapping.items() if k != self._sentinel}
