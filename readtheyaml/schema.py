import copy
import os
from pathlib import Path
import yaml
from typing import Any, Dict, Optional, Union

from .exceptions.format_error import FormatError
from .exceptions.validation_error import ValidationError
from .conditions import parse_when, evaluate_when
from .fields.field import Field
from .fields.field_factory import FIELD_FACTORY
from .fields.field_helpers import get_reserved_keywords_by_loaded_fields

class Schema:
    def __init__(
            self,
            name: str,
            description: str = "",
            required: bool = True,
            fields: Optional[Dict[str, Field]] = None,
            subsections: Optional[Dict[str, "Schema"]] = None,
            default: Any = None,
            has_default: bool = False,
            when: Any = None,
    ):
        self.name = name
        self.description = description
        self.required = required
        self.fields = fields or {}
        self.subsections = subsections or {}
        self.default = default
        self.has_default = has_default
        self.when = when

    def build_and_validate(
        self, data: Dict[str, Any], strict: bool = True, _condition_context: Optional[Dict[str, Any]] = None
    ) -> tuple[Dict[str, Any], Dict[str, Any]]:
        if not isinstance(data, dict):
            raise ValidationError(f"Section '{self.name or '<root>'}' expects a mapping/dictionary, got {type(data).__name__}")

        if _condition_context is None:
            _condition_context = self._build_condition_context(data)

        built_data = {}
        data_with_default = copy.deepcopy(data)

        for field_name, field in self.fields.items():
            if not evaluate_when(field.when, _condition_context):
                data_with_default.pop(field_name, None)
                continue

            from_default = False
            if field_name in data:
                value = data[field_name]
            elif field.required:
                raise ValidationError(f"Missing required field '{field_name}'")
            else:
                from_default = True
                value = copy.deepcopy(field.default)
                data_with_default[field_name] = copy.deepcopy(value)

            # Defaults are already validated/built by Field.post_init.
            # Re-validating them can be harmful for fields like ObjectField
            # where validate_and_build constructs instances.
            if not from_default:
                value = field.validate_and_build(value)

            built_data[field_name] = value

        # Validate subsections
        for section_name, subsection in self.subsections.items():
            if not evaluate_when(subsection.when, _condition_context):
                data_with_default.pop(section_name, None)
                continue

            if section_name in data:
                built_data[section_name], data_with_default[section_name] = subsection.build_and_validate(
                    data[section_name], strict=strict, _condition_context=_condition_context
                )
            elif subsection.required:
                raise ValidationError(f"Missing required section '{section_name}'")
            else:
                if subsection.has_default:
                    built_data[section_name] = copy.deepcopy(subsection.default)
                    data_with_default[section_name] = copy.deepcopy(subsection.default)
                else:
                    built_data[section_name], data_with_default[section_name] = subsection.build_and_validate(
                        {}, strict=strict, _condition_context=_condition_context
                    )

        # Handle extra keys
        allowed_keys = set(self.fields.keys()) | set(self.subsections.keys())
        if strict:
            unexpected_keys = set(data.keys()) - allowed_keys
            if unexpected_keys:
                raise ValidationError(f"Unexpected key(s) in section '{self.name or '<root>'}': {', '.join(sorted(unexpected_keys))}")
        else:
            for key in data:
                if key not in allowed_keys:
                    built_data[key] = data[key]

        return built_data, data_with_default

    def to_dict(self) -> dict:
        output = {
            "name": self.name,
            "description": self.description,
            "required": self.required,
            "fields": {k: v.to_dict() for k, v in self.fields.items()},
            "subsections": {k: v.to_dict() for k, v in self.subsections.items()},
        }
        if self.has_default:
            output["default"] = self.default
        if self.when is not None:
            output["when"] = copy.deepcopy(self.when)
        return output

    @classmethod
    def from_yaml(cls, schema_file: str, base_schema_dir: Optional[Union[str, Path]] = None) -> "Schema":
        if not os.path.isfile(schema_file):
            raise FileNotFoundError(f"Schema file not found: {schema_file}")

        # Default base dir to the folder containing the YAML file
        if base_schema_dir is None:
            base_schema_dir = Path(schema_file).resolve().parent
        else:
            base_schema_dir = Path(base_schema_dir)

        if not os.path.isdir(base_schema_dir):
            raise NotADirectoryError(f"Base schema directory does not exist: {base_schema_dir}")

        with open(schema_file, "r", encoding="utf-8") as f:
            data = cls._safe_load_yaml(f.read(), str(schema_file))

        return cls._from_dict(data, base_schema_dir)

    def validate_file(self, yaml_path: Union[str, Path], strict: bool = True):
        yaml_path = Path(yaml_path)
        with open(yaml_path, "r", encoding="utf-8") as f:
            config = self._safe_load_yaml(f.read(), str(yaml_path))

        return self.build_and_validate(config, strict=strict)

    @classmethod
    def _from_dict(cls, data: Dict[str, Any], base_schema_dir: Optional[Path] = None) -> "Schema":
        if not isinstance(data, dict):
            raise ValidationError(f"Schema definition must be a mapping/dictionary, got {type(data).__name__}")

        reserved_map = get_reserved_keywords_by_loaded_fields()
        all_reserved_keywords = set().union(*reserved_map.values())

        if base_schema_dir is None:
            base_schema_dir = Path(".")

        name = data.get("name", "")
        description = data.get("description", "")
        required = data.get("required", True)
        has_default = "default" in data
        default = data.get("default")
        when = None
        raw_when = data.get("when")
        has_section_when = "when" in data and not (
            isinstance(raw_when, dict) and ("type" in raw_when or "$ref" in raw_when)
        )
        if has_section_when:
            try:
                when = parse_when(raw_when, f"when for section '{name or '<root>'}'")
            except FormatError as e:
                raise ValidationError(str(e))

        fields: Dict[str, Field] = {}
        subsections: Dict[str, Schema] = {}

        for key, value in data.items():
            if key == "when" and has_section_when:
                continue
            if isinstance(value, dict):
                if "type" in value:
                    if key in all_reserved_keywords:
                        raise FormatError(
                            f"The field name '{key}' is reserved by one or more Field classes (e.g., used as constructor argument). Please choose a different name.")

                    try:
                        type_str = value["type"]
                        fields[key] = FIELD_FACTORY.create_field(type_str, key, **value)
                    except Exception as e:
                        raise ValidationError(f"Failed to build field '{key}': {e}")
                elif "$ref" in value:
                    ref_path = value["$ref"]
                    ref_dict, ref_base_dir = cls._resolve_ref_and_base(ref_path, base_schema_dir)
                    if not isinstance(ref_dict, dict):
                        raise ValidationError(f"Schema definition must be a mapping/dictionary, got {type(ref_dict).__name__}")
                    full_section_data = ref_dict.copy()
                    full_section_data.update({k: v for k, v in value.items() if k != "$ref"})

                    # Optional referenced sections should default to None unless explicitly overridden.
                    # This avoids implicitly materializing nested defaults when the whole section is absent.
                    if full_section_data.get("required", True) is False and "default" not in full_section_data:
                        full_section_data["default"] = None

                    subsection = cls._from_dict(full_section_data, base_schema_dir=ref_base_dir)
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
            default=default,
            has_default=has_default,
            when=when,
        )

    def _build_condition_context(self, data: Dict[str, Any]) -> Dict[str, Any]:
        context = copy.deepcopy(data)
        self._inject_defaults_for_condition_context(context)
        return context

    def _inject_defaults_for_condition_context(self, context: Dict[str, Any]) -> None:
        changed = True
        while changed:
            changed = False

            for field_name, field in self.fields.items():
                if field_name in context or field.required:
                    continue
                if not evaluate_when(field.when, context):
                    continue

                default_value = getattr(field, "raw_default", field.default)
                context[field_name] = copy.deepcopy(default_value)
                changed = True

            for section_name, subsection in self.subsections.items():
                if section_name in context:
                    section_value = context[section_name]
                    if isinstance(section_value, dict):
                        subsection._inject_defaults_for_condition_context(section_value)
                    continue

                if not evaluate_when(subsection.when, context):
                    continue
                if not subsection.has_default:
                    continue

                context[section_name] = copy.deepcopy(subsection.default)
                section_value = context[section_name]
                if isinstance(section_value, dict):
                    subsection._inject_defaults_for_condition_context(section_value)
                changed = True

    @staticmethod
    def _resolve_ref(ref: str, base_dir: Path) -> Dict[str, Any]:
        resolved, _ = Schema._resolve_ref_and_base(ref, base_dir)
        return resolved

    @staticmethod
    def _resolve_ref_and_base(ref: str, base_dir: Path) -> tuple[Dict[str, Any], Path]:
        if ref.startswith("https://") or ref.startswith("http://"):
            import requests
            resp = requests.get(ref, timeout=10)
            resp.raise_for_status()
            return Schema._safe_load_yaml(resp.text, ref), base_dir

        target = (base_dir / ref).resolve()
        if not target.exists():
            raise FileNotFoundError(f"Referenced schema file not found: {target}")
        with open(target, "r", encoding="utf-8") as f:
            return Schema._safe_load_yaml(f.read(), str(target)), target.parent

    @staticmethod
    def _safe_load_yaml(content: str, source: str) -> Any:
        try:
            return yaml.safe_load(content)
        except yaml.YAMLError as e:
            raise FormatError(f"Invalid YAML format in '{source}': {e}") from e
