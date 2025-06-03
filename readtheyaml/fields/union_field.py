from readtheyaml.exceptions.format_error import FormatError
from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.fields.field import Field
from readtheyaml.fields.string_field import StringField


class UnionField(Field):
    def __init__(self, options: list[Field], **kwargs):
        super().__init__(**kwargs)
        if "ignore_post" not in kwargs:
            kwargs["ignore_post"] = True

        # Check for duplicate field types and validate StringField casting
        field_types = []
        for option in options:
            # Get the actual class from the partial object
            field_class = option.func if hasattr(option, 'func') else option
            field_types.append(field_class.__name__)

            # Check if this is a StringField and if cast_to_string is True in either the partial or the kwargs
            if field_class is StringField:
                # Get cast_to_string from partial args if it exists, otherwise use True as default
                partial_args = getattr(option, "keywords", {})
                cast_to_string = partial_args.get("cast_to_string", False) or kwargs.get("cast_to_string", False)
                
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
            raise FormatError(
                f"Field '{self.name}': Duplicate field types found in UnionField: {', '.join(duplicates)}. "
                "Each field type should appear only once."
            )

        self._options = [curr_option(**kwargs) for curr_option in options]

    def validate(self, value):
        errors = []
        for field in self._options:
            try:
                validated_value = field.validate(value)
                return validated_value
            except ValidationError as e:
                errors.append(str(e))

        raise ValidationError(f"Field '{self.name}': {value!r} does not match any allowed type: {' | '.join(errors)}")
