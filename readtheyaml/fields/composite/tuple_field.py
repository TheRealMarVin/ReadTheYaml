import ast
import copy
from functools import partial
from typing import Sequence

from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.fields.field import Field
from readtheyaml.utils.type_utils import extract_types_for_composite, split_top_level


class TupleField(Field):
    def __init__(self, element_fields: Sequence[Field], **kwargs):
        super().__init__(**kwargs)

        self._slots = element_fields

    def validate_and_build(self, value):
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
                field.validate_and_build(v)
            except ValidationError as err:
                raise ValidationError(f"Field '{self.name}': Tuple element {idx} invalid: {err}")

        return value

    @staticmethod
    def from_type_string(type_str: str, name: str, factory, **kwargs) -> "Field":
        tuple_inner = extract_types_for_composite(type_str=type_str, type_name="tuple")
        if tuple_inner is not None:
            element_specs = split_top_level(tuple_inner, ',')

            args_copy = copy.deepcopy(kwargs)
            args_copy["ignore_post"] = True

            element_fields = []
            for element in element_specs:
                constructor = factory.create_field(element, name, **args_copy)
                element_fields.append(constructor)
            return TupleField(name=name, element_fields=element_fields, **kwargs)

        return None
