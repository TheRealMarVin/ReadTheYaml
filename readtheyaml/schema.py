import os
from pathlib import Path
import yaml
from typing import Any, Dict, Optional, Union

from .exceptions.validation_error import ValidationError
from .fields.field import Field
from .fields.field_helpers import build_field
from .sections import Section


class Schema(Section):
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
        if base_schema_dir is None:
            base_schema_dir = Path(".")

        name = data.get("name", "")
        description = data.get("description", "")
        required = data.get("required", True)

        fields: Dict[str, Field] = {}
        subsections: Dict[str, Section] = {}

        for key, value in data.items():
            if key in {"name", "description", "required"}:
                continue

            if isinstance(value, dict) and "type" in value:
                try:
                    fields[key] = build_field(value, key, base_schema_dir)
                except Exception as e:
                    raise ValidationError(f"Failed to build field '{key}': {e}")

            elif isinstance(value, dict):
                if "$ref" in value:
                    ref_path = value["$ref"]
                    ref_dict = cls._resolve_ref(ref_path, base_schema_dir)
                    full_section_data = ref_dict.copy()
                    full_section_data.update({k: v for k, v in value.items() if k != "$ref"})
                    subsection = cls._from_dict(full_section_data, base_schema_dir=base_schema_dir)
                else:
                    subsection = cls._from_dict(value, base_schema_dir=base_schema_dir)

                subsections[key] = subsection
            else:
                raise ValidationError(f"Cannot determine if '{key}' is a field or section.")

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
