from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.fields.field import Field
from readtheyaml.ui.widgets import BoolFieldWidget


class BoolField(Field):
    def __init__(self, *, when=None, **kwargs):
        super().__init__(when=when, field_type="bool", **kwargs)

    def validate_and_build(self, value):
        if type(value) == str:
            if value.lower() in {"none", "null", ""}:
                raise ValidationError(f"Field '{self.name}': Must be of type bool, contains None or null or empty")
            if value.lower() not in {"true", "false"}:
                raise ValidationError(f"Field '{self.name}': Expected a boolean value.")

            value = True if value.lower() in {"true"} else False
        else:
            if not isinstance(value, bool):
                raise ValidationError(f"Field '{self.name}': Expected a boolean value, got {type(value).__name__}")

        return value

    def ui_widget_type(self):
        return BoolFieldWidget

    @staticmethod
    def from_type_string(type_str: str, name: str, factory, **kwargs):
        if type_str in {"Bool", "bool", "BOOL"}:
            return BoolField(name=name, **kwargs)

        return None
