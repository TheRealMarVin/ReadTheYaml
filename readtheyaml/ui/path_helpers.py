from typing import Any, Dict

from readtheyaml.ui.constants import ROOT_PATH, ROOT_PATH_PREFIX


def normalize_path(path: str) -> str:
    if not path or path == ROOT_PATH:
        return ""
    if path.startswith(ROOT_PATH_PREFIX):
        return path[len(ROOT_PATH_PREFIX):]
    return path


def subsection_key(parent_section: Dict[str, Any], subsection: Dict[str, Any]) -> str:
    path = normalize_path(subsection.get("path", ""))
    parent_path = normalize_path(parent_section.get("path", ""))
    if not path:
        return ""
    if not parent_path:
        return path.split(".", 1)[0]
    prefix = f"{parent_path}."
    if path.startswith(prefix):
        return path[len(prefix):].split(".", 1)[0]
    return path.split(".")[-1]


def get_path_value(data: Dict[str, Any], dotted_path: str, default: Any = None) -> Any:
    if not dotted_path:
        return data
    current: Any = data
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]
    return current


def path_exists(data: Dict[str, Any], dotted_path: str) -> bool:
    if not dotted_path:
        return True
    current: Any = data
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            return False
        current = current[part]
    return True
