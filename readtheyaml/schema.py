import copy
import os
from pathlib import Path
import yaml
from typing import Any, Dict, Optional, Union

from .exceptions.format_error import FormatError
from .exceptions.validation_error import ValidationError
from .fields.field import Field
from .fields.field_helpers import build_field, get_reserved_keywords_by_loaded_fields

class Schema:
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

    def build_and_validate(self, data: Dict[str, Any], strict: bool = True) -> Dict[str, Any]:
        built_data = {}
        data_with_default = copy.deepcopy(data)

        for field_name, field in self.fields.items():
            if field_name in data:
                value = data[field_name]
            elif field.required:
                raise ValidationError(f"Missing required field '{field_name}'")
            else:
                value = field.default
                data_with_default[field_name] = value

            if value is not None:
                value = field.validate(value)

            built_data[field_name] = value

        # Validate subsections
        for section_name, subsection in self.subsections.items():
            if section_name in data:
                built_data[section_name], data_with_default[section_name] = subsection.build_and_validate(data[section_name], strict=strict)
            elif subsection.required:
                raise ValidationError(f"Missing required section '{section_name}'")
            else:
                built_data[section_name], data_with_default[section_name] = subsection.build_and_validate({}, strict=strict)

        # Handle extra keys
        allowed_keys = set(self.fields.keys()) | set(self.subsections.keys())
        if strict:
            unexpected_keys = set(data.keys()) - allowed_keys
            if unexpected_keys:
                raise ValidationError(
                    f"Unexpected key(s) in section '{self.name or '<root>'}': {', '.join(sorted(unexpected_keys))}"
                )
        else:
            for key in data:
                if key not in allowed_keys:
                    built_data[key] = data[key]

        return built_data, data_with_default

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "required": self.required,
            "fields": {k: v.to_dict() for k, v in self.fields.items()},
            "subsections": {k: v.to_dict() for k, v in self.subsections.items()},
        }

    @classmethod
    def from_yaml(cls, schema_file: str, base_schema_dir: str = None) -> "Schema":
        if not os.path.isfile(schema_file):
            raise FileNotFoundError(f"Schema file not found: {schema_file}")

        # Default base dir to the folder containing the YAML file
        if base_schema_dir is None:
            base_schema_dir = os.path.dirname(os.path.abspath(schema_file))

        if not os.path.isdir(base_schema_dir):
            raise NotADirectoryError(f"Base schema directory does not exist: {base_schema_dir}")

        with open(schema_file, "r") as f:
            data = yaml.safe_load(f)

        return cls._from_dict(data, base_schema_dir)

    def validate_file(self, yaml_path: Union[str, Path], strict: bool = True):
        yaml_path = Path(yaml_path)
        with open(yaml_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        return self.build_and_validate(config, strict=strict)

    @classmethod
    def _from_dict(cls, data: Dict[str, Any], base_schema_dir: Optional[Path] = None) -> "Schema":
        reserved_map = get_reserved_keywords_by_loaded_fields()
        all_reserved_keywords = set().union(*reserved_map.values())

        if base_schema_dir is None:
            base_schema_dir = Path(".")

        name = data.get("name", "")
        description = data.get("description", "")
        required = data.get("required", True)

        fields: Dict[str, Field] = {}
        subsections: Dict[str, Schema] = {}

        for key, value in data.items():
            if isinstance(value, dict):
                if "type" in value:
                    if key in all_reserved_keywords:
                        raise FormatError(
                            f"The field name '{key}' is reserved by one or more Field classes (e.g., used as constructor argument). Please choose a different name.")

                    try:
                        fields[key] = build_field(value, key, base_schema_dir)
                    except Exception as e:
                        raise ValidationError(f"Failed to build field '{key}': {e}")
                elif "$ref" in value:
                    ref_path = value["$ref"]
                    ref_dict = cls._resolve_ref(ref_path, base_schema_dir)
                    full_section_data = ref_dict.copy()
                    full_section_data.update({k: v for k, v in value.items() if k != "$ref"})
                    subsection = cls._from_dict(full_section_data, base_schema_dir=base_schema_dir)
                    subsections[key] = subsection
                else:
                    # Handle nested sections
                    subsection = cls._from_dict(value, base_schema_dir=base_schema_dir)
                    subsections[key] = subsection

        return cls(
            name=name,
            description=description,
            required=required,
            fields=fields,
            subsections=subsections,
        )

    @staticmethod
    def _resolve_ref(ref: str, base_dir: Path) -> Dict[str, Any]:
        if ref.startswith("http://") or ref.startswith("https://"):
            import requests
            resp = requests.get(ref, timeout=10)
            resp.raise_for_status()
            return yaml.safe_load(resp.text)

        target = (base_dir / ref).resolve()
        if not target.exists():
            raise FileNotFoundError(f"Referenced schema file not found: {target}")
        with open(target, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
