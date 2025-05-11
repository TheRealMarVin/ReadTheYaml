from typing import Dict

from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.fields.field import Field


class CompositeField(Field):
    def __init__(self, fields: Dict[str, Field] = None, **kwargs):
        super().__init__(**kwargs)
        self.fields = fields or {}

    def validate(self, value):
        if not isinstance(value, dict):
            raise ValidationError(f"Field '{self.name}': must be a dictionary.")

        result = {}
        for field_name, field in self.fields.items():
            if field.required and field_name not in value:
                raise ValidationError(f"Field '{self.name}': Missing required field '{field_name}' in '{self.name}'.")
            if field_name in value:
                result[field_name] = field.validate(value[field_name])
            elif field.default is not None:
                result[field_name] = field.default
        return result

    def __repr__(self):
        return f"<CompositeField {self.name} with {len(self.fields)} subfields>"
