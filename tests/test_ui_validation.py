from readtheyaml.schema import Schema
from readtheyaml.ui.validation import ValidationController, build_fix_hints, parse_validation_error


class FakeScheduler:
    def __init__(self):
        self.calls = []
        self.cancelled = []
        self._next_token = 1

    def schedule(self, delay_ms, callback):
        token = self._next_token
        self._next_token += 1
        self.calls.append((token, delay_ms, callback))
        return token

    def cancel(self, token):
        self.cancelled.append(token)

    def run_last(self):
        token, _, callback = self.calls[-1]
        callback()
        return token


def _schema_with_required_name():
    return Schema._from_dict(
        {
            "service_name": {
                "type": "str",
                "description": "service",
            }
        }
    )


def _schema_with_optional_section_required_field():
    return Schema._from_dict(
        {
            "compile": {
                "required": False,
                "command": {
                    "type": "str",
                    "description": "build command",
                    "required": True,
                },
            }
        }
    )


def test_parse_validation_error_field_level_message():
    field_errors, global_errors = parse_validation_error("Field 'service.port': Must be of type int")
    assert field_errors == {"service.port": "Must be of type int"}
    assert global_errors == []


def test_parse_validation_error_missing_required_field_message():
    field_errors, global_errors = parse_validation_error("Missing required field 'service_name'")
    assert field_errors == {"service_name": "Missing required field."}
    assert global_errors == []


def test_validation_controller_success_state():
    scheduler = FakeScheduler()
    states = []
    controller = ValidationController(
        schema=_schema_with_required_name(),
        strict=True,
        schedule_callback=scheduler.schedule,
        cancel_callback=scheduler.cancel,
        state_callback=states.append,
        debounce_ms=300,
    )

    controller.request_validation({"service_name": "demo"})
    assert scheduler.calls[-1][1] == 300
    scheduler.run_last()

    assert len(states) == 1
    state = states[0]
    assert state.is_valid is True
    assert state.field_errors == {}
    assert state.global_errors == []
    assert state.built_output["service_name"] == "demo"


def test_validation_controller_invalid_state_and_debounce_cancels_previous():
    scheduler = FakeScheduler()
    states = []
    controller = ValidationController(
        schema=_schema_with_required_name(),
        strict=True,
        schedule_callback=scheduler.schedule,
        cancel_callback=scheduler.cancel,
        state_callback=states.append,
        debounce_ms=300,
    )

    controller.request_validation({})
    first_token = scheduler.calls[-1][0]
    controller.request_validation({"service_name": "demo"})
    assert scheduler.cancelled == [first_token]
    scheduler.run_last()

    assert len(states) == 1
    assert states[0].is_valid is True


def test_validation_controller_surfaces_validation_error_without_crashing():
    scheduler = FakeScheduler()
    states = []
    controller = ValidationController(
        schema=_schema_with_required_name(),
        strict=True,
        schedule_callback=scheduler.schedule,
        cancel_callback=scheduler.cancel,
        state_callback=states.append,
        debounce_ms=300,
    )

    controller.request_validation({})
    scheduler.run_last()

    assert len(states) == 1
    state = states[0]
    assert state.is_valid is False
    assert state.field_errors == {"service_name": "Missing required field."}


def test_validation_controller_maps_required_error_to_enabled_optional_section_field():
    scheduler = FakeScheduler()
    states = []
    controller = ValidationController(
        schema=_schema_with_optional_section_required_field(),
        strict=True,
        schedule_callback=scheduler.schedule,
        cancel_callback=scheduler.cancel,
        state_callback=states.append,
        debounce_ms=300,
    )

    controller.request_validation({"compile": {}})
    scheduler.run_last()

    assert len(states) == 1
    state = states[0]
    assert state.is_valid is False
    assert state.field_errors == {"compile.command": "Missing required field."}


def test_validation_controller_maps_missing_required_section_to_nested_required_field():
    scheduler = FakeScheduler()
    states = []
    schema = Schema._from_dict(
        {
            "mode": {"type": "enum", "description": "mode", "values": ["dev", "prod"], "required": False, "default": "dev"},
            "deploy": {
                "when": {"field": "mode", "op": "eq", "value": "prod"},
                "required": True,
                "target": {"type": "str", "description": "target env", "required": True},
            },
        }
    )
    controller = ValidationController(
        schema=schema,
        strict=True,
        schedule_callback=scheduler.schedule,
        cancel_callback=scheduler.cancel,
        state_callback=states.append,
        debounce_ms=300,
    )

    controller.request_validation({"mode": "prod"})
    scheduler.run_last()

    assert len(states) == 1
    state = states[0]
    assert state.is_valid is False
    assert state.field_errors == {"deploy.target": "Missing required field."}


def test_validation_controller_reports_all_missing_required_fields_in_active_section():
    scheduler = FakeScheduler()
    states = []
    schema = Schema._from_dict(
        {
            "mode": {"type": "enum", "description": "mode", "values": ["dev", "prod"], "required": False, "default": "dev"},
            "deploy": {
                "when": {"field": "mode", "op": "eq", "value": "prod"},
                "required": False,
                "target": {"type": "str", "description": "target env", "required": True},
                "strategy": {"type": "str", "description": "strategy", "required": True},
            },
        }
    )
    controller = ValidationController(
        schema=schema,
        strict=True,
        schedule_callback=scheduler.schedule,
        cancel_callback=scheduler.cancel,
        state_callback=states.append,
        debounce_ms=300,
    )

    controller.request_validation({"mode": "prod", "deploy": {}})
    scheduler.run_last()

    assert len(states) == 1
    state = states[0]
    assert state.is_valid is False
    assert state.field_errors == {
        "deploy.target": "Missing required field.",
        "deploy.strategy": "Missing required field.",
    }


def test_validation_controller_reports_missing_required_fields_for_active_optional_section_when_absent():
    scheduler = FakeScheduler()
    states = []
    schema = Schema._from_dict(
        {
            "mode": {"type": "enum", "description": "mode", "values": ["dev", "prod"], "required": False, "default": "dev"},
            "deploy": {
                "when": {"field": "mode", "op": "eq", "value": "prod"},
                "required": False,
                "target": {"type": "str", "description": "target env", "required": True},
            },
        }
    )
    controller = ValidationController(
        schema=schema,
        strict=True,
        schedule_callback=scheduler.schedule,
        cancel_callback=scheduler.cancel,
        state_callback=states.append,
        debounce_ms=300,
    )

    controller.request_validation({"mode": "prod"})
    scheduler.run_last()

    assert len(states) == 1
    state = states[0]
    assert state.is_valid is False
    assert state.field_errors == {"deploy.target": "Missing required field."}


def test_build_fix_hints_for_missing_required_field():
    hints = build_fix_hints({"service_name": "Missing required field."}, [])
    assert hints == ["Add required key 'service_name' to your config."]


def test_build_fix_hints_for_bounds_violation():
    hints = build_fix_hints({"workers": "Value must be at most 8."}, [])
    assert hints == ["Set 'workers' to be at most 8."]


def test_build_fix_hints_for_type_mismatch():
    hints = build_fix_hints({"port": "Must be of type int"}, [])
    assert hints == ["Use value type 'int' for 'port'."]
