from typing import Any, Dict, Optional

from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.field import OldField


class Section:
    def __init__(
        self,
        name: str,
        description: str = "",
        required: bool = True,
        fields: Optional[Dict[str, OldField]] = None,
        subsections: Optional[Dict[str, 'Section']] = None,
    ):
        self.name = name
        self.description = description
        self.required = required
        self.fields = fields or {}
        self.subsections = subsections or {}

    def build_and_validate(self, config: Dict[str, Any], strict: bool = True) -> Dict[str, Any]:
        result = {}

        # Validate fields
        for field_name, field in self.fields.items():
            if field_name in config:
                value = config[field_name]
            elif field.required:
                raise ValidationError(f"Missing required field '{field_name}'")
            else:
                value = field.default

            if value is not None:
                if not isinstance(value, field.value_type):
                    raise ValidationError(f"Field '{field_name}' should be of type {field.value_type.__name__}")
                if field.value_range:
                    min_val, max_val = field.value_range
                    if field.value_type == list:
                        for v in value:
                            if not (min_val <= v <= max_val):
                                raise ValidationError(f"Field '{field_name}' must be between {min_val} and {max_val}")
                    else:
                        if not (min_val <= value <= max_val):
                            raise ValidationError(f"Field '{field_name}' must be between {min_val} and {max_val}")
                if field.length_range:
                    if len(field.length_range) == 2:
                        min_val, max_val = field.length_range
                        if min_val < 0:
                            raise ValidationError(
                                f"Field '{field_name}' lower bound of length_range({min_val}) is negative")
                        if max_val < 0:
                            raise ValidationError(
                                f"Field '{field_name}' upper bound of length_range({max_val}) is negative")
                        if max_val < min_val:
                            raise ValidationError(
                                f"Field '{field_name}' upper bound of length_range({max_val}) is lower than lower bound({min_val})")
                        if not (min_val <= len(value) <= max_val):
                            raise ValidationError(
                                f"Field '{field_name}' must have a length between {min_val} and {max_val}")
                    elif len(field.length_range) == 1:
                        val = field.length_range
                        if val < 0:
                            raise ValidationError(
                                f"Field '{field_name}' length_range({val}) is negative")
                        if not (len(value) == val):
                            raise ValidationError(
                                f"Field '{field_name}' must have a length {val}")
                    else:
                        raise ValidationError(f"Field '{field_name}' invalid number of element in length_range")

            result[field_name] = value

        # Validate subsections
        for section_name, subsection in self.subsections.items():
            if section_name in config:
                result[section_name] = subsection.build_and_validate(config[section_name], strict=strict)
            elif subsection.required:
                raise ValidationError(f"Missing required section '{section_name}'")
            else:
                # Add optional section with defaults if not present in config
                result[section_name] = subsection.build_and_validate({}, strict=strict)

        # Add unexpected keys if not in strict mode
        if not strict:
            allowed_keys = set(self.fields.keys()) | set(self.subsections.keys())
            for key in config:
                if key not in allowed_keys:
                    result[key] = config[key]

        # Check for unexpected keys in strict mode
        if strict:
            allowed_keys = set(self.fields.keys()) | set(self.subsections.keys())
            unexpected_keys = set(config.keys()) - allowed_keys
            if unexpected_keys:
                raise ValidationError(
                    f"Unexpected key(s) in section '{self.name or '<root>'}': {', '.join(sorted(unexpected_keys))}"
                )

        return result

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "required": self.required,
            "fields": {k: v.to_dict() for k, v in self.fields.items()},
            "subsections": {k: v.to_dict() for k, v in self.subsections.items()},
        }
