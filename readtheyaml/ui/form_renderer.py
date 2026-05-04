from copy import deepcopy
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Dict, Optional

from readtheyaml.conditions import evaluate_when
from readtheyaml.ui.widgets import INVALID_INPUT, BoolFieldWidget, EnumFieldWidget, FloatFieldWidget, IntFieldWidget, StringFieldWidget


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


def evaluate_visibility_map(section_model: Dict[str, Any], draft_config: Dict[str, Any]) -> Dict[str, bool]:
    visibility: Dict[str, bool] = {}
    _collect_visibility_recursive(section_model, draft_config, parent_active=True, visibility=visibility)
    return visibility


def resolve_display_value(field_model: Dict[str, Any], draft_config: Dict[str, Any], field_path: str) -> Any:
    current = get_value_at_path(draft_config, field_path, default=None)
    if current is not None:
        return current
    if field_model.get("has_default", False):
        return deepcopy(field_model.get("default"))
    return None


def _collect_visibility_recursive(section_model: Dict[str, Any], draft_config: Dict[str, Any], parent_active: bool, visibility: Dict[str, bool]):
    section_path = _normalize_path(section_model.get("path", ""))
    section_active = parent_active and evaluate_when(section_model.get("when"), draft_config)
    if section_path:
        visibility[section_path] = section_active

    for field in section_model.get("fields", []):
        field_path = _join_path(section_path, field["key"])
        visibility[field_path] = section_active and evaluate_when(field.get("when"), draft_config)

    for subsection in section_model.get("subsections", []):
        _collect_visibility_recursive(subsection, draft_config, parent_active=section_active, visibility=visibility)


class FormRenderer(ttk.Frame):
    def __init__(self, parent: tk.Misc, introspection_model: Dict[str, Any], current_config: Dict[str, Any], strict: bool = True, on_change: Optional[Callable[[Dict[str, Any]], None]] = None):
        super().__init__(parent)
        self._introspection_model = introspection_model
        self._strict = strict
        self._on_change = on_change
        self._widgets = {}
        self._section_views: Dict[str, Dict[str, Any]] = {}
        self._initializing = True
        if strict:
            self._draft_config = project_known_config(current_config, introspection_model)
        else:
            self._draft_config = deepcopy(current_config)

        self.columnconfigure(0, weight=1)
        self._render_section(self, introspection_model)
        self._refresh_when_visibility()
        self._initializing = False

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

    def focus_field(self, field_path: str):
        self._reveal_ancestors(field_path)
        widget = self._widgets.get(_normalize_path(field_path))
        if widget is None:
            return
        control = getattr(widget, "_input_widget", None)
        if control is not None:
            try:
                control.focus_set()
            except Exception:
                pass

    def reveal_section(self, section_path: str):
        self._reveal_ancestors(section_path)

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
        optional_checkbutton = None
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
                self._refresh_when_visibility()
                self._emit_change()

            optional_checkbutton = ttk.Checkbutton(header, text="enabled", variable=enabled_var, command=on_toggle_optional)
            optional_checkbutton.grid(row=0, column=2, sticky="w")
            if not enabled_var.get():
                body.grid_remove()
                toggle_text.set("[+]")
                collapsed.set(True)

        self._section_views[section_path] = {
            "container": container,
            "body": body,
            "collapsed": collapsed,
            "toggle_text": toggle_text,
            "enabled_var": enabled_var,
            "enabled_checkbutton": optional_checkbutton,
        }

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
        initial = resolve_display_value(field, self._draft_config, field_path)
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
        if self._initializing:
            return
        if value is INVALID_INPUT:
            self._remove_path(field_path)
            self._refresh_when_visibility()
            self._emit_change()
            return
        if value is None:
            self._remove_path(field_path)
            self._refresh_when_visibility()
            self._emit_change()
            return
        set_value_at_path(self._draft_config, field_path, value)
        self._refresh_when_visibility()
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

    def _refresh_when_visibility(self):
        # Hidden-value policy: retain hidden values in the in-memory draft, but treat visibility as
        # advisory UI state and exclude inactive branches from save payload construction.
        visibility = evaluate_visibility_map(self._introspection_model, self._draft_config)
        for path, widget in self._widgets.items():
            is_active = visibility.get(path, True)
            if is_active:
                widget.pack(fill="x", expand=True, pady=2)
            else:
                widget.pack_forget()
            self._set_widget_enabled(widget, is_active)

        for section_path, view in self._section_views.items():
            if not section_path:
                continue
            is_active = visibility.get(section_path, True)
            container = view["container"]
            body = view["body"]
            collapsed = view["collapsed"]
            toggle_text = view["toggle_text"]
            enabled_var = view["enabled_var"]
            checkbutton = view["enabled_checkbutton"]

            if is_active:
                container.pack(fill="x", expand=True, pady=4)
                if checkbutton is not None:
                    checkbutton.state(["!disabled"])
                is_optional_enabled = True if enabled_var is None else bool(enabled_var.get())
                if is_optional_enabled:
                    if collapsed.get():
                        body.grid_remove()
                        toggle_text.set("[+]")
                    else:
                        body.grid()
                        toggle_text.set("[-]")
                else:
                    body.grid_remove()
                    toggle_text.set("[+]")
            else:
                container.pack_forget()
                body.grid_remove()
                if checkbutton is not None:
                    checkbutton.state(["disabled"])
                toggle_text.set("[+]")

    @staticmethod
    def _set_widget_enabled(widget: Any, enabled: bool):
        control = getattr(widget, "_input_widget", None)
        if control is None:
            return
        try:
            if enabled:
                control.state(["!disabled"])
            else:
                control.state(["disabled"])
        except Exception:
            pass

    def _reveal_ancestors(self, path: str):
        normalized = _normalize_path(path)
        if not normalized:
            return
        parts = normalized.split(".")
        section_paths = []
        for i in range(1, len(parts) + 1):
            section_path = ".".join(parts[:i])
            if section_path in self._section_views:
                section_paths.append(section_path)

        for section_path in section_paths:
            view = self._section_views.get(section_path)
            if view is None:
                continue
            container = view["container"]
            body = view["body"]
            collapsed = view["collapsed"]
            toggle_text = view["toggle_text"]
            enabled_var = view["enabled_var"]
            checkbutton = view["enabled_checkbutton"]

            container.pack(fill="x", expand=True, pady=4)
            if checkbutton is not None:
                checkbutton.state(["!disabled"])
            if enabled_var is not None and not enabled_var.get():
                continue
            collapsed.set(False)
            toggle_text.set("[-]")
            body.grid()
