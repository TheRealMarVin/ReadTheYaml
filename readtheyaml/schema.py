from pathlib import Path
import yaml
from typing import Any, Dict, Optional, Union

from readtheyaml.exceptions.validation_error import ValidationError
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

        name = data.get("name", "")
        description = data.get("description", "")
        required = data.get("required", True)

        fields = {}
        subsections = {}

        for key, value in data.items():
            if key in {"name", "description", "required"}:
                continue

            if isinstance(value, dict) and (
                    "type" in value or "default" in value or "range" in value
            ):
                fields[key] = Field(
                    name=key,
                    description=value.get("description", ""),
                    required=value.get("required", True),
                    default=value.get("default"),
                    value_type=eval(value.get("type", "str")),
                    value_range=tuple(value.get("range", [])) or None,
                )
            elif isinstance(value, dict):
                if "$ref" in value:
                    ref_path = value["$ref"]
                    ref_dict = cls._resolve_ref(ref_path, base_dir)
                    full_section_data = ref_dict.copy()
                    full_section_data.update({k: v for k, v in value.items() if k != "$ref"})
                    subsection = cls._from_dict(full_section_data, base_dir=base_dir)
                else:
                    subsection = cls._from_dict(value, base_dir=base_dir)

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

    def validate_file(self, yaml_path: Union[str, Path], strict: bool = True):
        yaml_path = Path(yaml_path)
        with open(yaml_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        return self.build_and_validate(config, strict=strict)
