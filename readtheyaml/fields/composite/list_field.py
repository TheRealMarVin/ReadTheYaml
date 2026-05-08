import copy

from readtheyaml.exceptions.format_error import FormatError
from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.fields.field import Field
from readtheyaml.fields.field_validation_helpers import find_and_validate_bounds
from readtheyaml.utils.type_utils import extract_types_for_composite


class ListField(Field):
    def __init__(self, item_field, min_length=None, max_length=None, length_range=None, *, when=None, **kwargs):
        if not isinstance(item_field, Field):
            raise FormatError("ListField item_field must be a Field instance.")
        list_field_type = f"list({item_field.field_type()})"
        super().__init__(when=when, field_type=list_field_type, additional_allowed_kwargs={"min_length", "max_length", "length_range"}, **kwargs)

        self.item_field = item_field

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

    def constraint_specs(self):
        constraints = {"length_unit": "items"}
        if self.min_length is not None:
            constraints["min_length"] = self.min_length
        if self.max_length is not None:
            constraints["max_length"] = self.max_length
        item_constraints = self.item_field.constraint_specs()
        if item_constraints:
            constraints["item_constraints"] = item_constraints
        return constraints

    @staticmethod
    def from_type_string(type_str, name, factory, **kwargs):
        list_type = extract_types_for_composite(type_str=type_str, type_name="list")
        if list_type is not None:
            args_copy = copy.deepcopy(kwargs)
            args_copy["ignore_post"] = True
            args_copy["additional_allowed_kwargs"] = set(["min_length", "max_length", "length_range"])

            item_field = factory.create_field(list_type, name, **args_copy)
            return ListField(name=name, item_field=item_field, **kwargs)

        return None
