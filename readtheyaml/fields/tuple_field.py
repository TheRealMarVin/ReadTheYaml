import ast
from typing import Sequence

from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.fields.field import Field


class TupleField(Field):
    def __init__(self, element_fields: Sequence[Field], **kwargs):
        super().__init__(**kwargs)
        if "ignore_post" not in kwargs:
            kwargs["ignore_post"] = True
        self._slots = tuple([curr_field(**kwargs) for curr_field in element_fields])

    def validate(self, value):
        if value is None:
            raise ValidationError(f"Field '{self.name}': None is not a valid tuple")

        if type(value) != tuple:
            if not (value.startswith("(") and value.endswith(")")):
                raise ValidationError(f"Field '{self.name}': Not a valid tuple")

            value = ast.literal_eval(value)

            if type(value) != tuple:
                value = (value,)

        if not isinstance(value, tuple):
            raise ValidationError(f"Field '{self.name}': Expected tuple, got {type(value).__name__}")

        if len(value) != len(self._slots):
            raise ValidationError(f"Field '{self.name}': Tuple must contain exactly {len(self._slots)} elements (got {len(value)})")

        for idx, (v, field) in enumerate(zip(value, self._slots)):
            try:
                field.validate(v)
            except ValidationError as err:
                raise ValidationError(f"Field '{self.name}': Tuple element {idx} invalid: {err}")

        return value
