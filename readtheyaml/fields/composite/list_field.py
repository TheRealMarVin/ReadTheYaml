import inspect
from functools import partial
from typing import Optional

from readtheyaml.exceptions.format_error import FormatError
from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.fields.field import Field
from readtheyaml.fields.field_validation_helpers import find_and_validate_bounds, get_target_class
from readtheyaml.utils.type_utils import _extract_types_for_composite


class ListField(Field):
    def __init__(
        self,
        item_field: Field,                  # Field instance to validate each item
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        length_range: Optional[tuple[int, int]] = None,
        **kwargs
    ):
        sig = inspect.signature(get_target_class(item_field).__init__)
        super().__init__(additional_allowed_kwargs=set(sig.parameters), **kwargs)
        if "ignore_post" not in kwargs:
            kwargs["ignore_post"] = True
        self.item_field = item_field(**kwargs)

        try:
            self.min_length, self.max_length = find_and_validate_bounds(length_range, min_length, max_length)
        except FormatError as e:
            raise ValidationError(f"Field '{self.name}': {e}")

    def validate_and_build(self, value):
        if not isinstance(value, list):
            raise ValidationError(f"Field '{self.name}': Expected a list.")

        if self.min_length is not None and len(value) < self.min_length:
            raise ValidationError(f"Field '{self.name}': List must contain at least {self.min_length} items.")

        if self.max_length is not None and len(value) > self.max_length:
            raise ValidationError(f"Field '{self.name}': List must contain at most {self.max_length} items.")

        validated = []
        for i, item in enumerate(value):
            try:
                validated.append(self.item_field.validate_and_build(item))
            except ValidationError as e:
                raise ValidationError(f"Field '{self.name}': Invalid item at index {i}: {e}")

        return validated

    @staticmethod
    def from_type_string(type_str: str, name: str, factory, **kwargs) -> "Field":
        list_type = _extract_types_for_composite(type_str=type_str, type_name="list")
        if list_type is not None:
            constructor = factory.create_field(list_type, name, **kwargs)
            return partial(ListField, item_field=constructor)

        return None
