from typing import Any, Dict, Optional

from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.fields.field import Field


class Section:
    def __init__(
        self,
        name: str,
        description: str = "",
        required: bool = True,
        fields: Optional[Dict[str, Field]] = None,
        subsections: Optional[Dict[str, 'Section']] = None,
    ):
        """
        Create a new Section object, representing a logical grouping of configuration settings.
        
        A Section is a fundamental building block for defining configuration schemas. It can contain:
        - Fields: Individual configuration parameters with specific types and validation rules
        - Subsections: Nested sections for hierarchical configuration structures
        
        Sections are used to validate and process configuration data, ensuring it matches the
        expected structure and constraints defined in the schema.

        Parameters
        ----------
        name : str
            Unique name of the section. This will be used as the key in the configuration.
        description : str, optional
            A human-readable description of what this section represents (default: "").
        required : bool, optional
            Whether this section must be present in the configuration (default: True).
            If True and the section is missing, a ValidationError will be raised.
        fields : dict of str to `Field`, optional
            A mapping of field names to their respective Field objects.
            Fields represent individual configuration parameters within this section.
        subsections : dict of str to `Section`, optional
            A mapping of subsection names to their respective Section objects.
            This allows for nested configuration structures.
        """
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
                value = field.validate(value)

            result[field_name] = value

        # Validate subsections
        for section_name, subsection in self.subsections.items():
            if section_name in config:
                result[section_name] = subsection.build_and_validate(config[section_name], strict=strict)
            elif subsection.required:
                raise ValidationError(f"Missing required section '{section_name}'")
            else:
                result[section_name] = subsection.build_and_validate({}, strict=strict)

        # Handle extra keys
        allowed_keys = set(self.fields.keys()) | set(self.subsections.keys())
        if strict:
            unexpected_keys = set(config.keys()) - allowed_keys
            if unexpected_keys:
                raise ValidationError(
                    f"Unexpected key(s) in section '{self.name or '<root>'}': {', '.join(sorted(unexpected_keys))}"
                )
        else:
            for key in config:
                if key not in allowed_keys:
                    result[key] = config[key]

        return result

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "required": self.required,
            "fields": {k: v.to_dict() for k, v in self.fields.items()},
            "subsections": {k: v.to_dict() for k, v in self.subsections.items()},
        }
