from readtheyaml.exceptions.format_error import FormatError
from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.fields.field import Field


class UnionField(Field):
    def __init__(self, options: list[Field], **kwargs):
        super().__init__(**kwargs)
        if 'ignore_post' not in kwargs:
            kwargs["ignore_post"] = True
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
