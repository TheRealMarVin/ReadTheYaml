from typing import Optional

from readtheyaml.exceptions.format_error import FormatError
from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.fields.field import Field
from readtheyaml.fields.field_validation_helpers import find_and_validate_bounds


class NumericalField(Field):
    def __init__(self, value_type=int, min_value=None, max_value=None, value_range=None, **kwargs):
        super().__init__(**kwargs)

        self.value_type = value_type

        try:
            self.min_value, self.max_value = find_and_validate_bounds(value_range, min_value, max_value)
        except FormatError as e:
            raise ValidationError(f"Field '{self.name}': {e}")

    def validate(self, value):
        if self.min_value is not None and value < self.min_value:
            raise ValidationError(f"Field '{self.name}': Value must be at least {self.min_value}.")
        if self.max_value is not None and value > self.max_value:
            raise ValidationError(f"Field '{self.name}': Value must be at most {self.max_value}.")

        try:
            if value == "None":
                value = None
            else:
                value = self.value_type(value)
        except (TypeError, ValueError):
            raise ValidationError(f"Field '{self.name}': Must be of type {self.value_type.__name__}")

        return value