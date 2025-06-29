from functools import partial

from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.fields.field import Field


class NoneField(Field):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def validate_and_build(self, value):
        if str(value).lower() in {"none", "null"}:
            return None

        raise ValidationError(f"Field '{self.name}': must be null/None")

    @staticmethod
    def from_type_string(type_str: str, name: str, factory, **kwargs) -> "Field":
        if type_str == "None":
            return NoneField

        return None