import re
from typing import Any, Callable, Dict, List, Optional, Tuple

from readtheyaml.conditions import evaluate_when
from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.schema import Schema
from readtheyaml.ui.schema_introspect import flatten_field_paths, introspect_schema_dict


FIELD_ERROR_PATTERN = re.compile(r"^Field '([^']+)':\s*(.+)$")
MISSING_FIELD_PATTERN = re.compile(r"^Missing required field '([^']+)'$")
MISSING_SECTION_PATTERN = re.compile(r"^Missing required section '([^']+)'$")
AT_LEAST_PATTERN = re.compile(r"at least\s+(-?\d+(?:\.\d+)?)", re.IGNORECASE)
AT_MOST_PATTERN = re.compile(r"at most\s+(-?\d+(?:\.\d+)?)", re.IGNORECASE)
TYPE_NAME_PATTERN = re.compile(r"Expected\s+([A-Za-z_][A-Za-z0-9_]*)", re.IGNORECASE)


class ValidationState:
    def __init__(self, is_valid: bool, built_output: Optional[Dict[str, Any]], data_with_default: Optional[Dict[str, Any]], field_errors: Dict[str, str], global_errors: List[str]):
        self.is_valid = is_valid
        self.built_output = built_output
        self.data_with_default = data_with_default
        self.field_errors = field_errors
        self.global_errors = global_errors


def parse_validation_error(message: str) -> Tuple[Dict[str, str], List[str]]:
    field_errors: Dict[str, str] = {}
    global_errors: List[str] = []

    field_match = FIELD_ERROR_PATTERN.match(message)
    if field_match:
        field_errors[field_match.group(1)] = field_match.group(2)
        return field_errors, global_errors

    missing_match = MISSING_FIELD_PATTERN.match(message)
    if missing_match:
        field_name = missing_match.group(1)
        field_errors[field_name] = "Missing required field."
        return field_errors, global_errors

    global_errors.append(message)
    return field_errors, global_errors


def build_fix_hints(field_errors: Dict[str, str], global_errors: List[str]) -> List[str]:
    hints: List[str] = []

    for field_path, message in field_errors.items():
        lower = message.lower()

        if "missing required field" in lower:
            hints.append(f"Add required key '{field_path}' to your config.")
            continue

        min_match = AT_LEAST_PATTERN.search(message)
        max_match = AT_MOST_PATTERN.search(message)
        if min_match or max_match:
            if min_match and max_match:
                hints.append(f"Set '{field_path}' within bounds {min_match.group(1)}..{max_match.group(1)}.")
            elif min_match:
                hints.append(f"Set '{field_path}' to be at least {min_match.group(1)}.")
            else:
                hints.append(f"Set '{field_path}' to be at most {max_match.group(1)}.")
            continue

        if "must be of type" in lower or "expected" in lower:
            expected = _extract_expected_type(message)
            if expected:
                hints.append(f"Use value type '{expected}' for '{field_path}'.")
            else:
                hints.append(f"Adjust '{field_path}' to the expected type.")
            continue

    for message in global_errors:
        missing_match = MISSING_FIELD_PATTERN.match(message)
        if missing_match:
            hints.append(f"Add required key '{missing_match.group(1)}' to your config.")
            continue

        min_match = AT_LEAST_PATTERN.search(message)
        max_match = AT_MOST_PATTERN.search(message)
        if min_match or max_match:
            if min_match and max_match:
                hints.append(f"Update value within bounds {min_match.group(1)}..{max_match.group(1)}.")
            elif min_match:
                hints.append(f"Update value to be at least {min_match.group(1)}.")
            else:
                hints.append(f"Update value to be at most {max_match.group(1)}.")
            continue

    return hints


def _extract_expected_type(message: str) -> Optional[str]:
    if "must be of type" in message.lower():
        parts = message.split("Must be of type", 1)
        if len(parts) == 2:
            return parts[1].strip().rstrip(".")

    type_match = TYPE_NAME_PATTERN.search(message)
    if type_match:
        return type_match.group(1)
    return None


class ValidationController:
    def __init__(self, schema: Schema, strict: bool, schedule_callback: Callable[[int, Callable[[], None]], Any], cancel_callback: Callable[[Any], None], state_callback: Callable[[ValidationState], None], debounce_ms: int = 300):
        self.schema = schema
        self.strict = strict
        self._schema_model = introspect_schema_dict(schema)
        self._all_field_paths = flatten_field_paths(self._schema_model)
        self.schedule_callback = schedule_callback
        self.cancel_callback = cancel_callback
        self.state_callback = state_callback
        self.debounce_ms = debounce_ms
        self._pending_token = None
        self._pending_config: Optional[Dict[str, Any]] = None

    def request_validation(self, draft_config: Dict[str, Any]):
        self._pending_config = draft_config
        if self._pending_token is not None:
            self.cancel_callback(self._pending_token)
            self._pending_token = None
        self._pending_token = self.schedule_callback(self.debounce_ms, self._run_validation)

    def _run_validation(self):
        self._pending_token = None
        draft_config = self._pending_config or {}
        try:
            built_output, data_with_default = self.schema.build_and_validate(draft_config, strict=self.strict)
            state = ValidationState(
                is_valid=True,
                built_output=built_output,
                data_with_default=data_with_default,
                field_errors={},
                global_errors=[],
            )
        except ValidationError as exc:
            field_errors, global_errors = parse_validation_error(str(exc))
            section_errors = self._expand_missing_required_section_errors(global_errors, draft_config)
            field_errors.update(section_errors)
            field_errors.update(self._collect_all_missing_required_field_errors(draft_config))
            field_errors = self._resolve_unscoped_field_paths(field_errors, draft_config)
            state = ValidationState(
                is_valid=False,
                built_output=None,
                data_with_default=None,
                field_errors=field_errors,
                global_errors=global_errors,
            )
        except Exception as exc:
            state = ValidationState(
                is_valid=False,
                built_output=None,
                data_with_default=None,
                field_errors={},
                global_errors=[f"Validation crashed: {exc}"],
            )
        self.state_callback(state)

    def _resolve_unscoped_field_paths(self, field_errors: Dict[str, str], draft_config: Dict[str, Any]) -> Dict[str, str]:
        resolved: Dict[str, str] = {}
        for path, message in field_errors.items():
            if "." in path:
                resolved[path] = message
                continue
            candidates = [field_path for field_path in self._all_field_paths if field_path.split(".")[-1] == path]
            if not candidates:
                resolved[path] = message
                continue
            if len(candidates) == 1:
                resolved[candidates[0]] = message
                continue
            active_candidates = [candidate for candidate in candidates if self._parent_exists(draft_config, candidate)]
            if len(active_candidates) == 1:
                resolved[active_candidates[0]] = message
                continue
            resolved[path] = message
        return resolved

    def _expand_missing_required_section_errors(self, global_errors: List[str], draft_config: Dict[str, Any]) -> Dict[str, str]:
        expanded: Dict[str, str] = {}
        for message in global_errors:
            section_match = MISSING_SECTION_PATTERN.match(message)
            if not section_match:
                continue
            section_name = section_match.group(1)
            for section_path in self._candidate_section_paths(section_name, draft_config):
                section_model = self._find_section_model_by_path(self._schema_model, section_path)
                if not section_model:
                    continue
                for required_path in self._required_field_paths_for_section(section_model):
                    expanded[required_path] = "Missing required field."
        return expanded

    def _candidate_section_paths(self, section_name: str, draft_config: Dict[str, Any]) -> List[str]:
        candidates = [p for p in self._collect_section_paths(self._schema_model) if p.split(".")[-1] == section_name]
        if len(candidates) <= 1:
            return candidates
        active = [p for p in candidates if self._parent_exists(draft_config, p)]
        return active or candidates

    def _collect_section_paths(self, section_model: Dict[str, Any]) -> List[str]:
        paths: List[str] = []
        for subsection in section_model.get("subsections", []):
            path = self._normalize_path(subsection.get("path", ""))
            if path:
                paths.append(path)
            paths.extend(self._collect_section_paths(subsection))
        return paths

    def _find_section_model_by_path(self, section_model: Dict[str, Any], target_path: str) -> Optional[Dict[str, Any]]:
        if self._normalize_path(section_model.get("path", "")) == target_path:
            return section_model
        for subsection in section_model.get("subsections", []):
            found = self._find_section_model_by_path(subsection, target_path)
            if found is not None:
                return found
        return None

    def _required_field_paths_for_section(self, section_model: Dict[str, Any]) -> List[str]:
        section_path = self._normalize_path(section_model.get("path", ""))
        required_paths: List[str] = []
        for field in section_model.get("fields", []):
            if bool(field.get("required", True)):
                required_paths.append(self._join_path(section_path, field["key"]))
        for subsection in section_model.get("subsections", []):
            if bool(subsection.get("required", True)):
                required_paths.extend(self._required_field_paths_for_section(subsection))
        return required_paths

    def _collect_all_missing_required_field_errors(self, draft_config: Dict[str, Any]) -> Dict[str, str]:
        condition_context = self.schema._build_condition_context(draft_config)
        errors: Dict[str, str] = {}
        self._collect_missing_required_recursive(self._schema_model, draft_config, condition_context, errors)
        return errors

    def _collect_missing_required_recursive(
        self,
        section_model: Dict[str, Any],
        section_data: Any,
        condition_context: Dict[str, Any],
        errors: Dict[str, str],
    ) -> None:
        if not isinstance(section_data, dict):
            section_data = {}
        section_path = self._normalize_path(section_model.get("path", ""))

        for field in section_model.get("fields", []):
            if not evaluate_when(field.get("when"), condition_context):
                continue
            if not bool(field.get("required", True)):
                continue
            key = field["key"]
            if key not in section_data:
                errors[self._join_path(section_path, key)] = "Missing required field."

        for subsection in section_model.get("subsections", []):
            if not evaluate_when(subsection.get("when"), condition_context):
                continue
            subsection_key = self._subsection_key(section_model, subsection)
            subsection_data = section_data.get(subsection_key)
            is_required_subsection = bool(subsection.get("required", True))

            if subsection_data is None:
                if is_required_subsection:
                    for required_path in self._required_field_paths_for_section(subsection):
                        errors[required_path] = "Missing required field."
                continue

            if isinstance(subsection_data, dict):
                self._collect_missing_required_recursive(subsection, subsection_data, condition_context, errors)

    def _subsection_key(self, parent_section: Dict[str, Any], subsection: Dict[str, Any]) -> str:
        path = self._normalize_path(subsection.get("path", ""))
        parent_path = self._normalize_path(parent_section.get("path", ""))
        if not path:
            return ""
        if not parent_path:
            return path.split(".", 1)[0]
        prefix = f"{parent_path}."
        if path.startswith(prefix):
            return path[len(prefix):].split(".", 1)[0]
        return path.split(".")[-1]

    @staticmethod
    def _normalize_path(path: str) -> str:
        if not path or path == "<root>":
            return ""
        if path.startswith("<root>."):
            return path[len("<root>."):]
        return path

    @staticmethod
    def _join_path(prefix: str, key: str) -> str:
        if not prefix:
            return key
        return f"{prefix}.{key}"

    @staticmethod
    def _parent_exists(draft_config: Dict[str, Any], field_path: str) -> bool:
        parent = field_path.rsplit(".", 1)[0] if "." in field_path else ""
        if not parent:
            return True
        current: Any = draft_config
        for part in parent.split("."):
            if not isinstance(current, dict) or part not in current:
                return False
            current = current[part]
        return isinstance(current, dict)
