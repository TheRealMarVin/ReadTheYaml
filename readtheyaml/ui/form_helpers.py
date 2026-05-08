from copy import deepcopy
from typing import Any, Dict

from readtheyaml.conditions import evaluate_when
from readtheyaml.ui.path_helpers import normalize_path


def get_value_at_path(data: Dict[str, Any], dotted_path: str, default: Any = None):
    parts = _path_parts(dotted_path)
    if not parts:
        return default
    current: Any = data
    for part in parts:
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]
    return current


def set_value_at_path(data: Dict[str, Any], dotted_path: str, value: Any):
    parts = _path_parts(dotted_path)
    if not parts:
        return
    _, parent = _walk_path(data, parts[:-1], create_missing=True)
    parent[parts[-1]] = value


def materialize_section_path(data: Dict[str, Any], dotted_path: str):
    parts = _path_parts(dotted_path)
    if not parts:
        return data
    _, current = _walk_path(data, parts, create_missing=True)
    return current


def project_known_config(config: Dict[str, Any], section_model: Dict[str, Any]):
    projected = {}
    base_path = section_model.get("path", "")
    for field in section_model.get("fields", []):
        path = join_path(normalize_path(base_path), field["key"])
        value = get_value_at_path(config, path, default=None)
        if value is not None:
            set_value_at_path(projected, path, value)
    for subsection in section_model.get("subsections", []):
        nested = project_known_config(config, subsection)
        _merge_dict(projected, nested)
    return projected


def evaluate_visibility_map(section_model: Dict[str, Any], draft_config: Dict[str, Any]):
    visibility: Dict[str, bool] = {}
    _collect_visibility_recursive(section_model, draft_config, parent_active=True, visibility=visibility)
    return visibility


def resolve_display_value(field_model: Dict[str, Any], draft_config: Dict[str, Any], field_path: str):
    current = get_value_at_path(draft_config, field_path, default=None)
    if current is not None:
        return current
    if field_model.get("has_default", False):
        return deepcopy(field_model.get("default"))
    return None


def _path_parts(dotted_path: str):
    normalized_path = normalize_path(dotted_path)
    if not normalized_path:
        return []
    return normalized_path.split(".")


def _walk_path(data: Dict[str, Any], parts: list[str], create_missing: bool):
    current: Any = data
    for part in parts:
        if not isinstance(current, dict):
            return False, None
        if part not in current or not isinstance(current[part], dict):
            if not create_missing:
                return False, None
            current[part] = {}
        current = current[part]
    return True, current


def _merge_dict(target: Dict[str, Any], source: Dict[str, Any]):
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            _merge_dict(target[key], value)
        else:
            target[key] = deepcopy(value)


def join_path(prefix: str, key: str):
    if not prefix:
        return key
    return f"{prefix}.{key}"


def _normalize_path(path: str):
    # Backward-compatible alias for callers that still import the private helper.
    return normalize_path(path)


def _collect_visibility_recursive(section_model: Dict[str, Any], draft_config: Dict[str, Any], parent_active: bool, visibility: Dict[str, bool]):
    section_path = normalize_path(section_model.get("path", ""))
    section_active = parent_active and evaluate_when(section_model.get("when"), draft_config)
    if section_path:
        visibility[section_path] = section_active

    for field in section_model.get("fields", []):
        field_path = join_path(section_path, field["key"])
        visibility[field_path] = section_active and evaluate_when(field.get("when"), draft_config)

    for subsection in section_model.get("subsections", []):
        _collect_visibility_recursive(subsection, draft_config, parent_active=section_active, visibility=visibility)
