from functools import partial

from readtheyaml.exceptions.format_error import FormatError
from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.fields.field import Field


class EnumField(Field):
    def __init__(self, values=None, *, when=None, **kwargs):
        super().__init__(when=when, field_type="enum", **kwargs)
        if not values or not isinstance(values, (list, tuple) or (isinstance(values, (list, tuple)) and len(values) == 0)):
            raise FormatError(f"Field '{self.name}': EnumField requires a list of choices.")
        self.choices = values

    def validate_and_build(self, value):
        if value not in self.choices:
            raise ValidationError(f"Field '{self.name}': Invalid value '{value}', expected one of: {self.choices}")
        return value

    def ui_widget_type(self):
        from readtheyaml.ui.widgets import EnumFieldWidget
        return partial(EnumFieldWidget, choices=list(self.choices))

    def constraint_specs(self):
        return {"enum_values": list(self.choices)}

    @staticmethod
    def from_type_string(type_str: str, name: str, factory, **kwargs):
        if type_str in {"enum", "Enum", "ENUM"}:
            return EnumField(name=name, **kwargs)

        return None
