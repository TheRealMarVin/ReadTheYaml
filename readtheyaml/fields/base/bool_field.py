from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.fields.field import Field


class BoolField(Field):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

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

    @staticmethod
    def from_type_string(type_str: str, name: str, factory, **kwargs) -> "Field":
        if type_str in {"Bool", "bool", "BOOL"}:
            return BoolField(name=name, **kwargs)

        return None