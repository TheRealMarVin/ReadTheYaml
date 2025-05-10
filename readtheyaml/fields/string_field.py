from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.fields.field import Field


class StringField(Field):
    def __init__(self, min_length=0, max_length=-1, **kwargs):
        super().__init__(**kwargs)

        self.min_length = min_length
        self.max_length = max_length

        if max_length != -1 and max_length < min_length:
            raise ValidationError(f"Field '{self.name}' max_length{max_length} smaller than min_length{min_length}")

    def validate(self, value):
        try:
            value = str(value)
        except (TypeError, ValueError):
            raise ValidationError(f"Field '{self.name}' must be of type str")

        if len(value) < self.min_length:
            raise ValidationError(f"Field '{self.name}' : Value must be at least {self.min_length} characters.")

        if 0 < self.max_length < len(value):
            raise ValidationError(f"Field '{self.name}' : Value must be at max {self.max_length} characters.")

        return value