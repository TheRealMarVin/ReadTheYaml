from typing import Optional

from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.fields.field import Field


class ListField(Field):
    def __init__(
        self,
        item_field: Field,                  # Field instance to validate each item
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.item_field = item_field
        self.min_length = min_length
        self.max_length = max_length

    def validate(self, value):
        if not isinstance(value, list):
            raise ValidationError("Field '{self.name}': Expected a list.")

        if self.min_length is not None and len(value) < self.min_length:
            raise ValidationError(f"Field '{self.name}': List must contain at least {self.min_length} items.")

        if self.max_length is not None and len(value) > self.max_length:
            raise ValidationError(f"Field '{self.name}': List must contain at most {self.max_length} items.")

        validated = []
        for i, item in enumerate(value):
            try:
                validated.append(self.item_field.validate(item))
            except ValidationError as e:
                raise ValidationError(f"Field '{self.name}': Invalid item at index {i}: {e}")

        return validated
