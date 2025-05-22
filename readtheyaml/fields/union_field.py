from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.fields.field import Field


class UnionField(Field):
    def __init__(self, options: list[Field], **kwargs):
        super().__init__(**kwargs)
        self._options = [o(**kwargs) for o in options]

    def validate(self, value):
        errors = []
        for field in self._options:
            try:
                validated_value = field.validate(value)
                return validated_value
            except ValidationError as e:
                errors.append(str(e))

        raise ValidationError(f"Field '{self.name}': {value!r} does not match any allowed type: {' | '.join(errors)}")
