from readtheyaml.exceptions.format_error import FormatError
from readtheyaml.fields.field import Field


class AnyField(Field):
    def __init__(self, **kwargs):
        required = kwargs.get("required", True)
        if not required and "default" not in kwargs:
            field_name = kwargs.get("name", "<unknown>")
            raise FormatError(f"Field {field_name} optional AnyField must define an explicit default value.")
        super().__init__(**kwargs)

    def validate_and_build(self, value):
        return value

    @staticmethod
    def from_type_string(type_str: str, name: str, factory, **kwargs) -> "Field":
        if type_str in {"any", "Any", "ANY"}:
            return AnyField(name=name, **kwargs)
        return None
