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
            if self.min_value is not None and value_type(self.min_value) != self.min_value:
                raise FormatError(f"Min value ({type(self.min_value)}) is not of type of the field ({value_type}). This is confusing.")
            if self.max_value is not None and value_type(self.max_value) != self.max_value:
                raise FormatError(f"Max value ({type(self.max_value)}) is not of type of the field ({value_type}). This is confusing.")
        except FormatError as e:
            raise ValidationError(f"Field '{self.name}': {e}")

    def validate(self, value):
        try:
            if str(value).lower() in {"true", "false"}:
                raise ValidationError(f"Field '{self.name}': Must be of type {self.value_type.__name__}, contains True or False.")

            new_value = self.value_type(value)
            if isinstance(value, float) and self.value_type is int:
                if not value.is_integer():
                    raise ValidationError(f"Value ({type(value)}) is not of type of the field ({self.value_type}). Not good.")

            value = new_value
        except (TypeError, ValueError):
            raise ValidationError(f"Field '{self.name}': Must be of type {self.value_type.__name__}")

        if self.min_value is not None and value < self.min_value:
            raise ValidationError(f"Field '{self.name}': Value must be at least {self.min_value}.")
        if self.max_value is not None and value > self.max_value:
            raise ValidationError(f"Field '{self.name}': Value must be at most {self.max_value}.")

        return value