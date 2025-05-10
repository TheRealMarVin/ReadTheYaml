from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.fields.field import Field


class IntegerField(Field):
    def __init__(self, value_type=int, min_value=None, max_value=None, **kwargs):
        super().__init__(**kwargs)

        self.value_type = value_type
        self.min_value = min_value
        self.max_value = max_value

    def validate(self, value):
        if self.min_value is not None and value < self.min_value:
            raise ValidationError(f"Field '{self.name}': Value must be at least {self.min_value}.")
        if self.max_value is not None and value > self.max_value:
            raise ValidationError(f"Field '{self.name}': Value must be at most {self.max_value}.")

        try:
            value = self.value_type(value)
        except (TypeError, ValueError):
            raise ValidationError(f"Field '{self.name}': Must be of type {self.value_type.__name__}")

        return value