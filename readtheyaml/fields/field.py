from pygments.lexer import default

from readtheyaml.exceptions.format_error import FormatError
from readtheyaml.exceptions.validation_error import ValidationError


class PostInitMeta(type):
    def __call__(cls, *args, **kwargs):
        # This runs __new__, __init__, then our post_init hook
        obj = super().__call__(*args, **kwargs)
        if hasattr(obj, "post_init"):
            obj.post_init()
        return obj


class Field(metaclass=PostInitMeta):
    allowed_kwargs = {"type"}

    def __init__(self, name, description, required=True, default=None,
                 additional_allowed_kwargs=set(), ignore_post=False, **kwargs):
        self.name = name
        self.required = required
        self.default = default
        self.description = description
        self.ignore_post = ignore_post

        if default is not None and required:
            raise FormatError(f"Field {self.name} you are providing default value for a required field. This is useless.")

        unknown = set(kwargs) - self.allowed_kwargs - additional_allowed_kwargs
        if unknown:
            raise FormatError(f"{self.__class__.__name__} got unknown parameters: {unknown}")

    def post_init(self):
        if not self.required and not self.ignore_post:
            try:
                self.validate_and_build(self.default)
            except ValidationError as e:
                raise FormatError(f"Field {self.name} got invalid default value: {e}") from None

    def validate_and_build(self, value):
        raise NotImplementedError(f"Field '{self.name}': Each field must implement its own validate method.")

    @staticmethod
    def from_type_string(type_str: str, name: str, factory, **kwargs) -> "Field":
        raise NotImplementedError("Each field must implement its own from_type_string.")
