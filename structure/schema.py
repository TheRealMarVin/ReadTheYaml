from pathlib import Path

import yaml
from typing import Any, Dict, Optional

from exceptions.validation_error import ValidationError
from .fields import Field
from .sections import Section


class Schema(Section):
    """
    A Schema is a top-level Section that can be constructed from Python or a YAML schema definition.
    """

    @classmethod
    def from_yaml(self, yaml_path: str, base_dir) -> "Schema":
        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)
        return self._from_dict(data, base_dir)

    @classmethod
    def _from_dict(cls, data: Dict[str, Any], base_dir: Optional[Path] = None) -> "Schema":
        if base_dir is None:
            base_dir = Path(".")

        name = data.get("name", "root")
        description = data.get("description", "")
        required = data.get("required", True)

        fields = {
            field_name: Field(
                name=field_name,
                description=field_data.get("description", ""),
                required=field_data.get("required", True),
                default=field_data.get("default"),
                value_type=eval(field_data.get("type", "str")),
                value_range=tuple(field_data.get("range", [])) or None,
            )
            for field_name, field_data in data.get("fields", {}).items()
        }

        subsections = {}
        raw_subsections = data.get("subsections", {})

        if isinstance(raw_subsections, dict):
            for section_name, section_data in raw_subsections.items():
                if isinstance(section_data, dict) and "$ref" in section_data:
                    ref_path = section_data["$ref"]
                    ref_dict = cls._resolve_ref(ref_path, base_dir)

                    # Merge ref_dict into section_data (ref provides defaults)
                    full_section_data = ref_dict.copy()
                    full_section_data.update({
                        k: v for k, v in section_data.items() if k != "$ref"
                    })

                    subsection = cls._from_dict(full_section_data, base_dir=base_dir)
                else:
                    subsection = cls._from_dict(section_data, base_dir=base_dir)

                subsections[section_name] = subsection

        elif isinstance(raw_subsections, list):
            for item in raw_subsections:
                if not isinstance(item, dict):
                    raise ValidationError("Each subsection list item must be a mapping")

                if "$ref" in item:
                    ref_path = item["$ref"]
                    ref_dict = cls._resolve_ref(ref_path, base_dir)

                    full_section_data = ref_dict.copy()
                    full_section_data.update({k: v for k, v in item.items() if k != "$ref"})
                    subsection = cls._from_dict(full_section_data, base_dir=base_dir)
                    section_name = subsection.name
                else:
                    section_name = item.get("name")
                    if not section_name:
                        raise ValidationError("Subsection must have a name or $ref")
                    subsection = cls._from_dict(item, base_dir=base_dir)

                if section_name in subsections:
                    raise ValidationError(f"Duplicate subsection name: {section_name}")

                subsections[section_name] = subsection

        elif raw_subsections:
            raise ValidationError("'subsections' must be a mapping or a list")

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

    def validate_file(self, yaml_path: str) -> Dict[str, Any]:
        with open(yaml_path, "r") as f:
            config = yaml.safe_load(f)
        return self.build_and_validate(config)
