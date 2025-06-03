from readtheyaml.exceptions.format_error import FormatError
from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.fields.field import Field


class StringField(Field):
    def __init__(self, min_length=0, max_length=-1, cast_to_string=False, **kwargs):
        """
        A field that validates and optionally converts values to strings.

        Args:
            min_length: Minimum length of the string (inclusive)
            max_length: Maximum length of the string (inclusive, -1 for no limit)
            cast_to_string: If True, automatically convert non-string values to strings.
                           If False, only accept string values.
        """
        super().__init__(**kwargs)
        self.min_length = min_length
        self.max_length = max_length
        self.cast_to_string = cast_to_string

        if min_length < 0:
            raise FormatError(f"Field '{self.name}': min_length {min_length} smaller than 0")
        if max_length != -1 and max_length < min_length:
            raise FormatError(f"Field '{self.name}': max_length {max_length} smaller than min_length {min_length}")

    def validate(self, value):
        # Convert to string if casting is enabled
        if self.cast_to_string:
            try:
                value = str(value)
            except (TypeError, ValueError) as e:
                raise ValidationError(
                    f"Field '{self.name}': Could not convert value to string: {e}"
                )
        elif not isinstance(value, str):
            raise ValidationError(f"Field '{self.name}': Expected string, got {type(value).__name__}")

        # Check string constraints
        if len(value) < self.min_length:
            raise ValidationError(f"Field '{self.name}': Value must be at least {self.min_length} characters")

        if 0 < self.max_length < len(value):
            raise ValidationError(f"Field '{self.name}': Value must be at most {self.max_length} characters")
        return value
