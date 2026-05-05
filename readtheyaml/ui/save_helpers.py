from copy import deepcopy
from typing import Any, Dict, Optional, Tuple

import yaml

from readtheyaml.conditions import evaluate_when

SAVE_MODE_EXPORT = "export"
SAVE_MODE_FULL = "full"


def serialize_yaml(data: Dict[str, Any]) -> str:
    text = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
    if not text.endswith("\n"):
        text += "\n"
    return text


def can_save(is_valid: bool) -> Tuple[bool, Optional[str]]:
    if is_valid:
        return True, None
    return False, "Cannot save because config is invalid. Fix listed errors first."


def get_save_payload(
    mode: str,
    draft_config: Dict[str, Any],
    data_with_default: Optional[Dict[str, Any]],
    schema_model: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if mode == SAVE_MODE_EXPORT:
        payload: Dict[str, Any] = draft_config
        if schema_model is not None:
            payload = _exclude_inactive_branches(payload, schema_model)
            if data_with_default is not None:
                payload = _remove_schema_defaults(payload, schema_model)
        return payload
    if mode == SAVE_MODE_FULL:
        if data_with_default is None:
            raise ValueError("Validated data_with_default is not available.")
        if schema_model is None:
            return data_with_default
        return _exclude_inactive_branches(data_with_default, schema_model)
    raise ValueError(f"Unknown save mode: {mode}")


def _remove_schema_defaults(data_with_default: Dict[str, Any], section_model: Dict[str, Any]) -> Dict[str, Any]:
    pruned = deepcopy(data_with_default)
    _prune_section(pruned, section_model)
    return pruned


def _prune_section(data: Dict[str, Any], section_model: Dict[str, Any]) -> None:
    if not isinstance(data, dict):
        return

    for field in section_model.get("fields", []):
        if not field.get("has_default", False):
            continue
        key = field["key"]
        if key in data and data[key] == field.get("default"):
            del data[key]

    for subsection in section_model.get("subsections", []):
        subsection_key = _subsection_key(section_model, subsection)
        if subsection_key not in data or not isinstance(data[subsection_key], dict):
            continue
        _prune_section(data[subsection_key], subsection)
        if not data[subsection_key]:
            del data[subsection_key]


def _subsection_key(parent_section: Dict[str, Any], subsection: Dict[str, Any]) -> str:
    path = _normalize_path(subsection.get("path", ""))
    parent_path = _normalize_path(parent_section.get("path", ""))
    if not path:
        return ""
    if not parent_path:
        return path.split(".", 1)[0]
    prefix = f"{parent_path}."
    if path.startswith(prefix):
        return path[len(prefix):].split(".", 1)[0]
    return path.split(".")[-1]


def _normalize_path(path: str) -> str:
    if not path or path == "<root>":
        return ""
    if path.startswith("<root>."):
        return path[len("<root>."):]
    return path


def _exclude_inactive_branches(data: Dict[str, Any], section_model: Dict[str, Any]) -> Dict[str, Any]:
    pruned = deepcopy(data)
    _prune_inactive_section(pruned, section_model, root_data=pruned)
    return pruned


def _prune_inactive_section(section_data: Any, section_model: Dict[str, Any], root_data: Dict[str, Any]):
    if not isinstance(section_data, dict):
        return

    for field in section_model.get("fields", []):
        if evaluate_when(field.get("when"), root_data):
            continue
        section_data.pop(field["key"], None)

    for subsection in section_model.get("subsections", []):
        subsection_key = _subsection_key(section_model, subsection)
        if subsection_key not in section_data:
            continue
        if not evaluate_when(subsection.get("when"), root_data):
            del section_data[subsection_key]
            continue
        child = section_data.get(subsection_key)
        if not isinstance(child, dict):
            continue
        _prune_inactive_section(child, subsection, root_data=root_data)
        if not child:
            del section_data[subsection_key]
