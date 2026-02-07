import copy
from functools import partial

from readtheyaml.exceptions.format_error import FormatError
from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.fields.field import Field
from readtheyaml.fields.base.string_field import StringField
from readtheyaml.utils.type_utils import extract_types_for_composite, split_top_level


class UnionField(Field):
    def __init__(self, options, **kwargs):
        super().__init__(**kwargs)

        def get_field_type(opt):
            if isinstance(opt, partial):
                return opt.func
            if isinstance(opt, type):
                return opt
            return opt.__class__

        def get_partial_keywords(opt):
            if isinstance(opt, partial):
                return opt.keywords or {}
            return {}

        field_types = []
        for option in options:
            field_type = get_field_type(option)
            field_types.append(field_type)

            if field_type is StringField:
                partial_args = get_partial_keywords(option)
                cast_to_string = partial_args.get("cast_to_string", True)
                if cast_to_string:
                    raise FormatError(
                        f"Field '{self.name}': StringField with cast_to_string=True is not allowed in UnionField. "
                        "Please set cast_to_string=False for StringField in UnionField or handle string conversion explicitly."
                    )

        seen_types = set()
        duplicates = set()
        for field_type in field_types:
            if field_type in seen_types:
                duplicates.add(field_type)
            seen_types.add(field_type)

        if duplicates:
            duplicates_names = ", ".join(t.__name__ for t in duplicates)
            raise FormatError(
                f"Field '{self.name}': Duplicate field types found in UnionField: {duplicates_names}. "
                "Each field type should appear only once."
            )

        self._options = options

    def _make_option_field(self, option):
        if isinstance(option, partial):
            return option()
        if isinstance(option, type):
            return option()
        return option

    def validate_and_build(self, value):
        errors = []
        for option in self._options:
            field = self._make_option_field(option)
            try:
                return field.validate_and_build(value)
            except ValidationError as e:
                errors.append(str(e))

        raise ValidationError(f"Field '{self.name}': {value!r} does not match any allowed type: {' | '.join(errors)}")

    @staticmethod
    def from_type_string(type_str: str, name: str, factory, **kwargs) -> "Field":
        # TODO content of the if are the same
        if '|' in type_str:
            parts = split_top_level(type_str, '|')
            parsed_fields = []

            args_copy = copy.deepcopy(kwargs)
            args_copy["ignore_post"] = True
            for part in parts:
                constructor = factory.create_field(part, name, **args_copy)
                parsed_fields.append(constructor)
            return UnionField(name=name, options=parsed_fields, **kwargs)

        union_inner = extract_types_for_composite(type_str=type_str, type_name="union")
        if union_inner:
            parts = split_top_level(union_inner, ',')
            parsed_fields = []

            args_copy = copy.deepcopy(kwargs)
            args_copy["ignore_post"] = True

            for part in parts:
                constructor = factory.create_field(part, name, **args_copy)
                parsed_fields.append(constructor)
            return UnionField(name=name, options=parsed_fields, **kwargs)

        return None