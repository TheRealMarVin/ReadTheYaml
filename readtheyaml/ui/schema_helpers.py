from typing import Any, Dict, List

from readtheyaml.ui.form_helpers import join_path


def flatten_field_paths(section: Dict[str, Any]):
    paths: List[str] = []
    for field in section.get("fields", []):
        paths.append(join_path(section["path"], field["key"]))
    for subsection in section.get("subsections", []):
        paths.extend(flatten_field_paths(subsection))
    return paths
