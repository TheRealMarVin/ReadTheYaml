from typing import Any, Dict, Optional

from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.fields import Field


class Section:
    def __init__(
        self,
        name: str,
        description: str = "",
        required: bool = True,
        fields: Optional[Dict[str, Field]] = None,
        subsections: Optional[Dict[str, 'Section']] = None,
    ):
        self.name = name
        self.description = description
        self.required = required
        self.fields = fields or {}
        self.subsections = subsections or {}

    def build_and_validate(self, config: Dict[str, Any]) -> Dict[str, Any]:
        if config is None:
            if self.required:
                raise ValidationError(f"Missing required section '{self.name}'")

            # If the section is optional, check if we can auto-populate it
            has_required_fields = any(field.required for field in self.fields.values())
            has_required_subsections = any(sub.required for sub in self.subsections.values())
            if has_required_fields or has_required_subsections:
                # Not safe to auto-add this section
                return {}

            # All fields/subsections are optional — populate with defaults
            config = {}

        result = {}

        # Validate fields
        for field_name, field in self.fields.items():
            try:
                value = config.get(field_name, None)
                validated = field.validate(value)
                result[field_name] = validated
            except ValidationError as e:
                raise ValidationError(f"In section '{self.name}': {e}")

        # Validate subsections
        for subsection_name, subsection in self.subsections.items():
            subconfig = config.get(subsection_name, None)
            try:
                validated_sub = subsection.build_and_validate(subconfig)
                if validated_sub or subsection.required:
                    result[subsection_name] = validated_sub
            except ValidationError as e:
                raise ValidationError(f"In section '{self.name}.{subsection_name}': {e}")

        return result

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "required": self.required,
            "fields": {k: v.to_dict() for k, v in self.fields.items()},
            "subsections": {k: v.to_dict() for k, v in self.subsections.items()},
        }
