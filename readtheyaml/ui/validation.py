import re
from typing import Any, Callable, Dict, List, Optional, Tuple

from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.schema import Schema


FIELD_ERROR_PATTERN = re.compile(r"^Field '([^']+)':\s*(.+)$")
MISSING_FIELD_PATTERN = re.compile(r"^Missing required field '([^']+)'$")


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


class ValidationController:
    def __init__(self, schema: Schema, strict: bool, schedule_callback: Callable[[int, Callable[[], None]], Any], cancel_callback: Callable[[Any], None], state_callback: Callable[[ValidationState], None], debounce_ms: int = 300):
        self.schema = schema
        self.strict = strict
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
