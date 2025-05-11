from readtheyaml.exceptions.format_error import FormatError
from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.fields.field import Field


class EnumField(Field):
    def __init__(self, values, **kwargs):
        super().__init__(**kwargs)
        if not values or not isinstance(values, (list, tuple)):
            raise FormatError(f"Field '{self.name}': EnumField requires a list of choices.")
        self.choices = values

    def validate(self, value):
        if value not in self.choices:
            raise ValidationError(f"Field '{self.name}': Invalid value '{value}', expected one of: {self.choices}")
        return value
