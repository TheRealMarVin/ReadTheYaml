from readtheyaml.exceptions.format_error import FormatError


class Field:
    allowed_kwargs = {"type"}

    def __init__(self, name, required=True, default=None,
                 description="Default Definition",
                 additional_allowed_kwargs=set(),
                 **kwargs):
        self.name = name
        self.required = required
        self.default = default
        self.description = description
        unknown = set(kwargs) - self.allowed_kwargs - additional_allowed_kwargs
        if unknown:
            raise FormatError(f"{self.__class__.__name__} got unknown parameters: {unknown}")

    def validate(self, value):
        raise NotImplementedError(f"Field '{self.name}': Each field must implement its own validate method.")
