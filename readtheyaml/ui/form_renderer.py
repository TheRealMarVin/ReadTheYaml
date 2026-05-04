from copy import deepcopy
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Dict, Optional

from readtheyaml.ui.widgets import BoolFieldWidget, EnumFieldWidget, FloatFieldWidget, IntFieldWidget, StringFieldWidget


def get_value_at_path(data: Dict[str, Any], dotted_path: str, default: Any = None) -> Any:
    dotted_path = _normalize_path(dotted_path)
    if not dotted_path:
        return default
    current = data
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]
    return current


def set_value_at_path(data: Dict[str, Any], dotted_path: str, value: Any):
    dotted_path = _normalize_path(dotted_path)
    if not dotted_path:
        return
    parts = dotted_path.split(".")
    current = data
    for part in parts[:-1]:
        if part not in current or not isinstance(current[part], dict):
            current[part] = {}
        current = current[part]
    current[parts[-1]] = value


def materialize_section_path(data: Dict[str, Any], dotted_path: str) -> Dict[str, Any]:
    dotted_path = _normalize_path(dotted_path)
    if not dotted_path:
        return data
    current = data
    for part in dotted_path.split("."):
        if part not in current or not isinstance(current[part], dict):
            current[part] = {}
        current = current[part]
    return current


def project_known_config(config: Dict[str, Any], section_model: Dict[str, Any]) -> Dict[str, Any]:
    projected = {}
    base_path = section_model.get("path", "")
    for field in section_model.get("fields", []):
        path = _join_path(base_path, field["key"])
        value = get_value_at_path(config, path, default=None)
        if value is not None:
            set_value_at_path(projected, path, value)
    for subsection in section_model.get("subsections", []):
        nested = project_known_config(config, subsection)
        _merge_dict(projected, nested)
    return projected


def _merge_dict(target: Dict[str, Any], source: Dict[str, Any]):
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            _merge_dict(target[key], value)
        else:
            target[key] = deepcopy(value)


def _join_path(prefix: str, key: str) -> str:
    prefix = _normalize_path(prefix)
    if not prefix:
        return key
    return f"{prefix}.{key}"


def _normalize_path(path: str) -> str:
    if not path or path == "<root>":
        return ""
    if path.startswith("<root>."):
        return path[len("<root>."):]
    return path


class FormRenderer(ttk.Frame):
    def __init__(self, parent: tk.Misc, introspection_model: Dict[str, Any], current_config: Dict[str, Any], strict: bool = True, on_change: Optional[Callable[[Dict[str, Any]], None]] = None):
        super().__init__(parent)
        self._introspection_model = introspection_model
        self._strict = strict
        self._on_change = on_change
        self._widgets = {}
        if strict:
            self._draft_config = project_known_config(current_config, introspection_model)
        else:
            self._draft_config = deepcopy(current_config)

        self.columnconfigure(0, weight=1)
        self._render_section(self, introspection_model)

    def get_current_config_dict(self) -> Dict[str, Any]:
        return deepcopy(self._draft_config)

    def set_on_change(self, callback: Optional[Callable[[Dict[str, Any]], None]]):
        self._on_change = callback

    def apply_field_errors(self, field_errors: Dict[str, str]):
        for field_path, widget in self._widgets.items():
            _ = field_path
            widget.clear_invalid()
        for field_path, error_message in field_errors.items():
            if field_path in self._widgets:
                self._widgets[field_path].mark_invalid(error_message)

    def _render_section(self, parent: ttk.Frame, section: Dict[str, Any]):
        section_path = section.get("path", "")
        title = section_path.split(".")[-1] if section_path else "<root>"

        container = ttk.Frame(parent)
        container.pack(fill="x", expand=True, pady=4)
        container.columnconfigure(0, weight=1)

        header = ttk.Frame(container)
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(2, weight=1)

        body = ttk.Frame(container)
        body.grid(row=1, column=0, sticky="ew")
        body.columnconfigure(0, weight=1)

        collapsed = tk.BooleanVar(value=False)
        toggle_text = tk.StringVar(value="[-]")

        def toggle():
            is_collapsed = not collapsed.get()
            collapsed.set(is_collapsed)
            if is_collapsed:
                toggle_text.set("[+]")
                body.grid_remove()
            else:
                toggle_text.set("[-]")
                body.grid()

        ttk.Button(header, textvariable=toggle_text, width=3, command=toggle).grid(row=0, column=0, sticky="w")
        ttk.Label(header, text=title).grid(row=0, column=1, sticky="w", padx=(4, 8))

        is_required = bool(section.get("required", True))
        enabled_var = None
        if not is_required and section_path:
            enabled_var = tk.BooleanVar(value=(get_value_at_path(self._draft_config, section_path, None) is not None))

            def on_toggle_optional():
                if enabled_var is None:
                    return
                if enabled_var.get():
                    materialize_section_path(self._draft_config, section_path)
                    body.grid()
                    toggle_text.set("[-]")
                    collapsed.set(False)
                else:
                    self._remove_path(section_path)
                    body.grid_remove()
                    toggle_text.set("[+]")
                    collapsed.set(True)
                self._emit_change()

            ttk.Checkbutton(header, text="enabled", variable=enabled_var, command=on_toggle_optional).grid(row=0, column=2, sticky="w")
            if not enabled_var.get():
                body.grid_remove()
                toggle_text.set("[+]")
                collapsed.set(True)

        for field in section.get("fields", []):
            field_path = _join_path(section_path, field["key"])
            widget = self._create_field_widget(body, field, field_path)
            widget.pack(fill="x", expand=True, pady=2)
            self._widgets[field_path] = widget

        for subsection in section.get("subsections", []):
            self._render_section(body, subsection)

    def _create_field_widget(self, parent: ttk.Frame, field: Dict[str, Any], field_path: str):
        field_type = field.get("type")
        label = field["key"]
        description = field.get("description", "")
        required = bool(field.get("required", True))
        widget_cls, kwargs = self._resolve_widget_type(field_type, field)
        on_change = lambda value, p=field_path: self._on_widget_change(p, value)
        widget = widget_cls(parent, label=label, description=description, required=required, on_change=on_change, **kwargs)
        initial = get_value_at_path(self._draft_config, field_path, None)
        widget.set_value(initial)
        return widget

    def _resolve_widget_type(self, field_type: str, field: Dict[str, Any]):
        if field_type == "str":
            return StringFieldWidget, {}
        if field_type == "int":
            return IntFieldWidget, {}
        if field_type == "float":
            return FloatFieldWidget, {}
        if field_type == "bool":
            return BoolFieldWidget, {}
        if field_type == "enum":
            constraints = field.get("constraints", {})
            return EnumFieldWidget, {"choices": list(constraints.get("enum_values", []))}
        return StringFieldWidget, {}

    def _on_widget_change(self, field_path: str, value: Any):
        set_value_at_path(self._draft_config, field_path, value)
        self._emit_change()

    def _remove_path(self, dotted_path: str):
        parts = dotted_path.split(".")
        current = self._draft_config
        stack = []
        for part in parts[:-1]:
            if part not in current or not isinstance(current[part], dict):
                return
            stack.append((current, part))
            current = current[part]
        if parts[-1] not in current:
            return
        del current[parts[-1]]
        while stack:
            parent, key = stack.pop()
            node = parent.get(key)
            if isinstance(node, dict) and not node:
                del parent[key]
            else:
                break

    def _emit_change(self):
        if self._on_change is not None:
            self._on_change(self.get_current_config_dict())
