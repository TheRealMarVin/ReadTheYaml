from typing import Any, Callable, Optional, Union

from readtheyaml.exceptions.validation_error import ValidationError


class Field:
    def __init__(
        self,
        name: str,
        description: str,
        required: bool = True,
        default: Any = None,
        value_type: type = str,
        value_range: Optional[tuple[Union[int, float], Union[int, float]]] = None,
        custom_validator: Optional[Callable[[Any], bool]] = None,
        element_type: Optional[type] = None,
        length_range: Optional[tuple[int, int]] = None
    ):
        self.name = name
        self.description = description
        self.required = required
        self.default = default
        self.value_type = value_type
        self.value_range = value_range
        self.custom_validator = custom_validator
        self.element_type = element_type
        self.length_range = length_range

        if not required and default is None:
            raise ValueError(f"Field '{name}' is optional but has no default value")

    def validate(self, value: Any) -> Any:
        if value is None:
            if self.required:
                raise ValidationError(f"Missing required field '{self.name}'")
            return self.default

        # Type check (list and dict bypass cast)
        if self.value_type in (list, dict):
            if not isinstance(value, self.value_type):
                raise ValidationError(
                    f"Field '{self.name}' must be of type {self.value_type.__name__}"
                )
            if self.length_range:
                min_len, max_len = self.length_range
                if not (min_len <= len(value) <= max_len):
                    raise ValidationError(
                        f"Field '{self.name}' must contain between {min_len} and {max_len} elements"
                    )
        else:
            try:
                value = self.value_type(value)
            except (TypeError, ValueError):
                raise ValidationError(
                    f"Field '{self.name}' must be of type {self.value_type.__name__}"
                )

        # Range check
        if self.value_range is not None:
            min_val, max_val = self.value_range
            if self.value_type in (int, float):
                if not (min_val <= value <= max_val):
                    raise ValidationError(
                        f"Field '{self.name}' must be between {min_val} and {max_val}"
                    )
            elif self.value_type == list:
                if not (min_val <= len(value) <= max_val):
                    raise ValidationError(
                        f"Field '{self.name}' must be a list of length between {min_val} and {max_val}"
                    )

        # Element type check
        if self.value_type == list and self.element_type:
            for i, item in enumerate(value):
                if not isinstance(item, self.element_type):
                    raise ValidationError(
                        f"Field '{self.name}' element at index {i} must be of type {self.element_type.__name__}"
                    )

        # Custom validator
        if self.custom_validator is not None and not self.custom_validator(value):
            raise ValidationError(f"Custom validation failed for field '{self.name}'")

        return value

    def build_and_validate(self, config: dict) -> Any:
        value = config.get(self.name, None)
        validated_value = self.validate(value)
        config[self.name] = validated_value
        return validated_value

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "required": self.required,
            "default": self.default,
            "type": self.value_type.__name__,
            "range": self.value_range,
            "element_type": self.element_type.__name__ if self.element_type else None,
        }
