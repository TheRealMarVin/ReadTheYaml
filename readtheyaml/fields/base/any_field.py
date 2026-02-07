from readtheyaml.fields.field import Field


class AnyField(Field):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def validate_and_build(self, value):
        return value

    @staticmethod
    def from_type_string(type_str: str, name: str, factory, **kwargs) -> "Field":
        return AnyField(name=name, **kwargs)
