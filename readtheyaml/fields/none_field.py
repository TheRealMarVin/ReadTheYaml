from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.fields.field import Field


class NoneField(Field):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def validate(self, value):
        if str(value).lower() in {"none", "null"}:
            return None

        raise ValidationError(f"Field '{self.name}': must be null/None")
