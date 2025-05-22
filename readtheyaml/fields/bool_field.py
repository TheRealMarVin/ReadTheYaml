from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.fields.field import Field


class BoolField(Field):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def validate(self, value):
        try:
            if type(value) == str and value.lower() in {"none", "null"}:
                raise ValidationError(f"Field '{self.name}': Must be of type bool, contains None or null")

            value = bool(value)
        except (TypeError, ValueError):
            raise ValidationError(f"Field '{self.name}': Must be of type bool")

        return value