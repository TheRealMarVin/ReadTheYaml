import argparse
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from readtheyaml.exceptions.format_error import FormatError
from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.conditions import format_when_human, parse_when
from readtheyaml.schema import Schema
from readtheyaml.schema_doc import format_field_constraints_for_display
from readtheyaml.ui.form_renderer import FormRenderer, evaluate_visibility_map
from readtheyaml.ui.save_helpers import SAVE_MODE_EXPORT, SAVE_MODE_FULL, can_save, get_save_payload, serialize_yaml
from readtheyaml.ui.schema_introspect import introspect_schema_dict
from readtheyaml.ui.validation import ValidationController, ValidationState, build_fix_hints
from readtheyaml.ui.widgets import normalize_enum, normalize_float, normalize_int, normalize_str


def _parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"true", "1", "yes", "y"}:
        return True
    if normalized in {"false", "0", "no", "n"}:
        return False
    raise argparse.ArgumentTypeError(f"Invalid boolean value: {value!r}. Use true or false.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Launch the ReadTheYAML Tkinter editor.")
    parser.add_argument("--schema", required=True, help="Path to the YAML schema definition file")
    parser.add_argument("--config", help="Path to a YAML config file")
    parser.add_argument("--strict", type=_parse_bool, default=True, help="Strict validation mode (true|false, default: true)")
    return parser


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    return build_parser().parse_args(argv)


def load_schema_and_config(schema_path: str, config_path: Optional[str], strict: bool) -> Tuple[Schema, Dict[str, Any]]:
    schema = Schema.from_yaml(schema_path)
    if config_path is None:
        config_data: Any = {}
    else:
        with open(config_path, "r", encoding="utf-8") as handle:
            config_data = Schema._safe_load_yaml(handle.read(), str(config_path))
        if config_data is None:
            config_data = {}
    if not isinstance(config_data, dict):
        raise ValidationError(f"Config root must be a mapping/dictionary, got {type(config_data).__name__}")
    return schema, config_data


def _show_startup_error(message: str):
    try:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("ReadTheYAML Editor", message)
        root.destroy()
    except tk.TclError:
        pass


class EditorApp:
    def __init__(self, schema_path: str, config_path: Optional[str], strict: bool, schema: Schema, config_data: Dict[str, Any]):
        self.schema_path = schema_path
        self.config_path = config_path
        self.strict = strict
        self.schema = schema
        self.model = introspect_schema_dict(schema)

        self.dirty = False
        self.validation_state = ValidationState(
            is_valid=False,
            built_output=None,
            data_with_default=None,
            field_errors={},
            global_errors=["Validation pending..."],
        )

        self.root = tk.Tk()
        self.root.geometry("1200x760")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_layout()
        self._build_schema_tree()
        self._refresh_save_controls()
        self._create_form(config_data)
        self._wire_validation()
        self._refresh_title_status()

    def _build_layout(self):
        paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned.grid(row=0, column=0, sticky="nsew")

        self.left = ttk.Frame(paned, padding=8)
        self.right = ttk.Frame(paned, padding=8)
        paned.add(self.left, weight=1)
        paned.add(self.right, weight=1)

        self.toolbar = ttk.Frame(self.left)
        self.toolbar.pack(fill="x", pady=(0, 6))
        ttk.Button(self.toolbar, text="Load config", command=self._on_load_config).pack(side="left", padx=(0, 6))
        self.save_button = ttk.Button(self.toolbar, text="Save", command=self._on_save)
        self.save_button.pack(side="left", padx=(0, 6))
        self.save_as_button = ttk.Button(self.toolbar, text="Save As", command=self._on_save_as)
        self.save_as_button.pack(side="left")

        ttk.Label(self.left, text="Schema").pack(anchor="w", pady=(0, 6))
        self.tree = ttk.Treeview(self.left, columns=("kind", "value"), show="tree headings", selectmode="browse")
        self.tree.heading("#0", text="Name", anchor="w")
        self.tree.heading("kind", text="Type", anchor="w")
        self.tree.heading("value", text="Value", anchor="w")
        self.tree.column("#0", width=240, stretch=True)
        self.tree.column("kind", width=90, stretch=False)
        self.tree.column("value", width=220, stretch=True)
        tree_scroll = ttk.Scrollbar(self.left, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")
        self.tree.bind("<Double-1>", self._on_tree_double_click)
        self.tree.tag_configure("missing_required", foreground="#b00020")
        self.tree.tag_configure("valid_value", foreground="#1f7a1f")
        self.tree.tag_configure("inactive", foreground="#808080")

        # Hidden host for form/state management; editing now happens from the tree.
        self.form_host = ttk.Frame(self.root)

        self.badge = tk.Label(self.right, text="PENDING", bg="#888888", fg="white", padx=8, pady=4)
        self.badge.pack(anchor="w", pady=(0, 8))

        ttk.Label(self.right, text="Global Errors", anchor="w").pack(fill="x")
        self.error_text = tk.Text(self.right, height=8, wrap="word")
        self.error_text.pack(fill="x", pady=(0, 8))

        ttk.Label(self.right, text="How to fix", anchor="w").pack(fill="x")
        self.hint_text = tk.Text(self.right, height=6, wrap="word")
        self.hint_text.pack(fill="x", pady=(0, 8))

        self.preview_tabs = ttk.Notebook(self.right)
        self.preview_tabs.pack(fill="both", expand=True)
        export_tab = ttk.Frame(self.preview_tabs)
        full_tab = ttk.Frame(self.preview_tabs)
        self.preview_tabs.add(export_tab, text="Export YAML")
        self.preview_tabs.add(full_tab, text="Full YAML (with defaults)")
        self.preview_tabs.select(0)

        self.export_text = tk.Text(export_tab, wrap="none")
        self.export_text.pack(fill="both", expand=True)
        self.full_text = tk.Text(full_tab, wrap="none")
        self.full_text.pack(fill="both", expand=True)

        self.status = ttk.Label(self.root, anchor="w")
        self.status.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))

    def _build_schema_tree(self):
        self._tree_item_to_path: Dict[str, tuple[str, str]] = {}
        self._field_path_to_item: Dict[str, str] = {}
        self._field_required: Dict[str, bool] = {}
        self._field_defaults: Dict[str, tuple[bool, Any]] = {}
        self._field_meta: Dict[str, Dict[str, Any]] = {}
        self._section_meta: Dict[str, Dict[str, Any]] = {}
        self._section_path_to_item: Dict[str, str] = {}
        self.tree.delete(*self.tree.get_children())
        root_item = self.tree.insert("", "end", text=self.model.get("name") or "<root>", values=("section", ""), open=True)
        self._tree_item_to_path[root_item] = ("section", "")
        self._section_path_to_item[""] = root_item
        self._section_meta[""] = self.model
        self._add_tree_nodes(root_item, self.model)

    def _add_tree_nodes(self, parent_item: str, section_model: Dict[str, Any]):
        section_path = self._normalize_path(section_model.get("path", ""))
        for field in section_model.get("fields", []):
            field_path = f"{section_path}.{field['key']}" if section_path else field["key"]
            type_name = field.get("type", "")
            node = self.tree.insert(parent_item, "end", text=field["key"], values=(type_name, ""))
            self._tree_item_to_path[node] = ("field", field_path)
            self._field_path_to_item[field_path] = node
            self._field_required[field_path] = bool(field.get("required", True))
            self._field_defaults[field_path] = (bool(field.get("has_default", False)), field.get("default"))
            self._field_meta[field_path] = field

        for subsection in section_model.get("subsections", []):
            subsection_path = self._normalize_path(subsection.get("path", ""))
            label = subsection_path.split(".")[-1] if subsection_path else (subsection.get("name") or "<root>")
            node = self.tree.insert(parent_item, "end", text=label, values=("section", ""), open=False)
            self._tree_item_to_path[node] = ("section", subsection_path)
            self._section_path_to_item[subsection_path] = node
            self._section_meta[subsection_path] = subsection
            self._add_tree_nodes(node, subsection)

    def _on_tree_double_click(self, event: tk.Event):
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return
        mapping = self._tree_item_to_path.get(item_id)
        if mapping is None:
            return
        node_kind, path = mapping
        if node_kind == "section":
            self._open_section_info_dialog(path)
            return
        if node_kind != "field":
            return
        self._open_tree_edit_dialog(path)

    def _open_section_info_dialog(self, section_path: str):
        section = self._section_meta.get(section_path)
        if section is None:
            return

        display_name = section.get("name") or (section_path.split(".")[-1] if section_path else "<root>")
        required_text = "required" if bool(section.get("required", True)) else "optional"
        display_path = section_path or "<root>"

        dialog = tk.Toplevel(self.root)
        dialog.title(f"Section: {display_name}")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)
        dialog.columnconfigure(0, weight=1)

        body = ttk.Frame(dialog, padding=12)
        body.grid(row=0, column=0, sticky="nsew")
        body.columnconfigure(0, weight=1)

        ttk.Label(body, text=f"{display_name} ({required_text})").grid(row=0, column=0, sticky="w")
        ttk.Label(body, text=f"Path: {display_path}").grid(row=1, column=0, sticky="w", pady=(2, 0))

        description = section.get("description", "") or "-"
        ttk.Label(body, text=f"Description: {description}", wraplength=520, justify="left").grid(row=2, column=0, sticky="w", pady=(8, 0))

        when = section.get("when")
        next_row = 3
        if when:
            when_text = self._format_when_text(when)
            if when_text:
                ttk.Label(body, text=f"Conditions: {when_text}", wraplength=520, justify="left").grid(row=next_row, column=0, sticky="w", pady=(4, 0))
                next_row += 1

        button_bar = ttk.Frame(body)
        button_bar.grid(row=next_row + 1, column=0, sticky="e", pady=(12, 0))
        ttk.Button(button_bar, text="OK", command=dialog.destroy).pack(side="right")

        dialog.update_idletasks()
        dialog.geometry(f"720x{dialog.winfo_reqheight()}")
        dialog.wait_window()

    @staticmethod
    def _normalize_path(path: str) -> str:
        if not path or path == "<root>":
            return ""
        if path.startswith("<root>."):
            return path[len("<root>."):]
        return path

    def _create_form(self, config_data: Dict[str, Any]):
        for child in self.form_host.winfo_children():
            child.destroy()
        self.form_renderer = FormRenderer(self.form_host, self.model, config_data, strict=self.strict)
        self.form_renderer.pack(fill="both", expand=True)
        self.form_renderer.set_on_change(self._on_form_change)
        self._refresh_tree_values()

    def _wire_validation(self):
        self.controller = ValidationController(
            schema=self.schema,
            strict=self.strict,
            schedule_callback=lambda delay, cb: self.root.after(delay, cb),
            cancel_callback=lambda token: self.root.after_cancel(token),
            state_callback=self._on_validation_state,
            debounce_ms=300,
        )
        self.controller.request_validation(self.form_renderer.get_current_config_dict())

    def _set_text(self, widget: tk.Text, value: str):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", value)
        widget.configure(state="disabled")

    def _refresh_title_status(self):
        schema_name = Path(self.schema_path).name
        config_name = Path(self.config_path).name if self.config_path else "<none>"
        dirty_mark = "*" if self.dirty else ""
        self.root.title(f"ReadTheYAML Editor - schema: {schema_name} | config: {config_name}{dirty_mark}")
        self.status.configure(text=f"Schema: {schema_name}    Config: {config_name}{dirty_mark}    Strict: {self.strict}")

    def _refresh_previews(self):
        draft = self.form_renderer.get_current_config_dict()
        if self.validation_state.is_valid and self.validation_state.data_with_default is not None:
            export_payload = get_save_payload(
                SAVE_MODE_EXPORT,
                draft,
                self.validation_state.data_with_default,
                schema_model=self.model,
            )
            full_payload = get_save_payload(
                SAVE_MODE_FULL,
                draft,
                self.validation_state.data_with_default,
                schema_model=self.model,
            )
            export_yaml = serialize_yaml(export_payload)
            full_yaml = serialize_yaml(full_payload)
        else:
            export_yaml = serialize_yaml(draft)
            full_yaml = ""
        self._set_text(self.export_text, export_yaml)
        self._set_text(self.full_text, full_yaml)

    def _on_form_change(self, _: Dict[str, Any]):
        self.dirty = True
        self._refresh_title_status()
        self._refresh_tree_values()
        self._refresh_previews()
        self.controller.request_validation(self.form_renderer.get_current_config_dict())

    def _refresh_save_controls(self):
        state = "normal" if self.validation_state.is_valid else "disabled"
        self.save_button.configure(state=state)
        self.save_as_button.configure(state=state)

    def _show_save_blocked(self):
        ok, reason = can_save(self.validation_state.is_valid)
        if ok:
            return False
        errors = list(self.validation_state.global_errors)
        for field_path, msg in sorted(self.validation_state.field_errors.items()):
            errors.append(f"{field_path}: {msg}")
        hints = build_fix_hints(self.validation_state.field_errors, self.validation_state.global_errors)
        detail = "\n".join(errors + [""] + hints).strip()
        message = reason or "Cannot save."
        if detail:
            message += f"\n\n{detail}"
        messagebox.showerror("Save blocked", message)
        return True

    def _on_validation_state(self, state: ValidationState):
        self.validation_state = state
        self.form_renderer.apply_field_errors(state.field_errors)
        self._refresh_tree_values()
        self._refresh_tree_node_colors()
        self._refresh_save_controls()

        if state.is_valid:
            self.badge.configure(text="VALID", bg="#1f7a1f")
            self._set_text(self.error_text, "")
            self._set_text(self.hint_text, "")
        else:
            self.badge.configure(text="INVALID", bg="#a32121")
            errors = list(state.global_errors)
            for path, msg in sorted(state.field_errors.items()):
                errors.append(f"{path}: {msg}")
            self._set_text(self.error_text, "\n".join(errors))
            self._set_text(self.hint_text, "\n".join(build_fix_hints(state.field_errors, state.global_errors)))
        self._refresh_previews()

    def _refresh_tree_node_colors(self):
        draft = self.form_renderer.get_current_config_dict()
        visibility = evaluate_visibility_map(self.model, draft)
        normalized_errors: Dict[str, str] = {}
        for raw_path, message in self.validation_state.field_errors.items():
            normalized = self._normalize_path(raw_path)
            resolved = self._resolve_tree_field_path(normalized)
            if resolved is None:
                normalized_errors[normalized] = message
            else:
                normalized_errors[resolved] = message

        for section_path, item_id in self._section_path_to_item.items():
            self.tree.item(item_id, tags=())
            if section_path and visibility.get(section_path, True) is False:
                self.tree.item(item_id, tags=("inactive",))

        for field_path, item_id in self._field_path_to_item.items():
            self.tree.item(item_id, tags=())
            if visibility.get(field_path, True) is False:
                self.tree.item(item_id, tags=("inactive",))
                continue

            has_value = self._path_exists(draft, field_path)
            error = normalized_errors.get(field_path, "")
            is_missing_required_error = error.strip().lower() == "missing required field."

            if is_missing_required_error and self._field_required.get(field_path, False):
                self.tree.item(item_id, tags=("missing_required",))
                continue

            if has_value and field_path not in normalized_errors:
                self.tree.item(item_id, tags=("valid_value",))

    def _resolve_tree_field_path(self, field_path: str) -> Optional[str]:
        if field_path in self._field_path_to_item:
            return field_path

        leaf = field_path.split(".")[-1] if field_path else ""
        if not leaf:
            return None
        candidates = [
            path for path in self._field_path_to_item
            if path == leaf or path.endswith(f".{leaf}")
        ]
        if len(candidates) == 1:
            return candidates[0]
        if leaf in self._field_path_to_item:
            return leaf
        return None

    def _refresh_tree_values(self):
        draft = self.form_renderer.get_current_config_dict()
        for field_path, item_id in self._field_path_to_item.items():
            has_value = self._path_exists(draft, field_path)
            if has_value:
                value = self._get_path_value(draft, field_path)
                value_text = self._format_tree_value(value)
            else:
                has_default, default_value = self._field_defaults.get(field_path, (False, None))
                if has_default and default_value is not None:
                    value_text = f"{self._format_tree_value(default_value)} (default)"
                else:
                    value_text = ""
            kind_text = self.tree.set(item_id, "kind")
            self.tree.item(item_id, values=(kind_text, value_text))

    def _open_tree_edit_dialog(self, field_path: str):
        field = self._field_meta.get(field_path)
        if field is None:
            return

        draft = self.form_renderer.get_current_config_dict()
        has_explicit_value = self._path_exists(draft, field_path)
        current_value = self._get_path_value(draft, field_path) if has_explicit_value else None
        has_default, default_value = self._field_defaults.get(field_path, (False, None))
        start_value = current_value if has_explicit_value else (default_value if has_default else None)

        dialog = tk.Toplevel(self.root)
        dialog.title(f"Edit value: {field_path}")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)
        dialog.columnconfigure(0, weight=1)

        body = ttk.Frame(dialog, padding=12)
        body.grid(row=0, column=0, sticky="nsew")
        body.columnconfigure(0, weight=1)

        required_text = "required" if bool(field.get("required", True)) else "optional"
        ttk.Label(body, text=f"{field_path} ({required_text})").grid(row=0, column=0, sticky="w")
        ttk.Label(body, text=f"Type: {field.get('type', '')}").grid(row=1, column=0, sticky="w", pady=(2, 0))

        description = field.get("description", "") or "-"
        ttk.Label(body, text=f"Description: {description}", wraplength=520, justify="left").grid(row=2, column=0, sticky="w", pady=(8, 0))
        next_row = 3
        if field.get("when"):
            when_text = self._format_when_text(field.get("when"))
            if when_text:
                ttk.Label(body, text=f"Conditions: {when_text}", wraplength=520, justify="left").grid(row=next_row, column=0, sticky="w", pady=(4, 0))
                next_row += 1
        constraints_text = self._format_constraints_text(field)
        if constraints_text:
            ttk.Label(body, text=f"Constraints: {constraints_text}", wraplength=520, justify="left").grid(row=next_row, column=0, sticky="w", pady=(4, 0))
            next_row += 1

        input_row = next_row
        if field.get("has_default", False) and field.get("default") is not None:
            ttk.Label(body, text=f"Default: {self._format_default_text(field)}", wraplength=520, justify="left").grid(row=input_row, column=0, sticky="w", pady=(4, 0))
            input_row += 1

        input_frame = ttk.Frame(body)
        input_frame.grid(row=input_row, column=0, sticky="ew", pady=(10, 0))
        input_frame.columnconfigure(0, weight=1)

        field_type = str(field.get("type", "str"))
        required = bool(field.get("required", True))
        constraints = field.get("constraints", {})
        enum_choices = list(constraints.get("enum_values", []))

        error_var = tk.StringVar(value="")
        parsed_value_holder: Dict[str, Any] = {"value": None}

        ok_button: Optional[ttk.Button] = None

        def set_validation(is_valid: bool, error: str = "", parsed: Any = None):
            error_var.set(error)
            parsed_value_holder["value"] = parsed
            if ok_button is not None:
                ok_button.configure(state="normal" if is_valid else "disabled")

        if field_type == "bool":
            var = tk.BooleanVar(value=bool(start_value))
            control = ttk.Checkbutton(input_frame, text="Enabled", variable=var)
            control.grid(row=0, column=0, sticky="w")

            def validate_bool(*_: Any):
                set_validation(True, "", bool(var.get()))

            var.trace_add("write", validate_bool)
            validate_bool()
        elif field_type == "enum":
            var = tk.StringVar(value="" if start_value is None else str(start_value))
            control = ttk.Combobox(input_frame, textvariable=var, values=enum_choices, state="readonly")
            control.grid(row=0, column=0, sticky="ew")

            def validate_enum(*_: Any):
                result = normalize_enum(var.get(), enum_choices)
                if result.error:
                    set_validation(False, result.error, None)
                    return
                set_validation(True, "", result.value)

            var.trace_add("write", validate_enum)
            validate_enum()
        else:
            var = tk.StringVar(value="" if start_value is None else str(start_value))
            control = ttk.Entry(input_frame, textvariable=var)
            control.grid(row=0, column=0, sticky="ew")

            def validate_entry(*_: Any):
                text_value = var.get()
                if field_type == "int":
                    result = normalize_int(text_value, required=required)
                elif field_type == "float":
                    result = normalize_float(text_value, required=required)
                else:
                    result = normalize_str(text_value, required=required)
                if result.error:
                    set_validation(False, result.error, None)
                    return
                set_validation(True, "", result.value)

            var.trace_add("write", validate_entry)
            validate_entry()

        ttk.Label(body, textvariable=error_var, foreground="#b00020").grid(row=input_row + 1, column=0, sticky="w", pady=(8, 0))

        button_bar = ttk.Frame(body)
        button_bar.grid(row=input_row + 2, column=0, sticky="e", pady=(12, 0))
        ttk.Button(button_bar, text="Cancel", command=dialog.destroy).pack(side="right")

        def on_ok():
            self.form_renderer.set_field_value(field_path, parsed_value_holder["value"])
            dialog.destroy()

        ok_button = ttk.Button(button_bar, text="OK", command=on_ok, state="disabled")
        ok_button.pack(side="right", padx=(0, 8))

        # Run once again now that ok_button exists.
        if field_type == "bool":
            set_validation(True, "", bool(var.get()))
        elif field_type == "enum":
            result = normalize_enum(var.get(), enum_choices)
            set_validation(result.error is None, result.error or "", result.value if result.error is None else None)
        else:
            text_value = var.get()
            if field_type == "int":
                result = normalize_int(text_value, required=required)
            elif field_type == "float":
                result = normalize_float(text_value, required=required)
            else:
                result = normalize_str(text_value, required=required)
            set_validation(result.error is None, result.error or "", result.value if result.error is None else None)

        control.focus_set()
        dialog.update_idletasks()
        dialog.geometry(f"720x{dialog.winfo_reqheight()}")
        dialog.wait_window()

    @staticmethod
    def _format_when_text(when: Any) -> str:
        if not when:
            return ""
        try:
            if isinstance(when, dict) and "kind" in when:
                human = format_when_human(when)
            else:
                human = format_when_human(parse_when(when, "when"))
            return f"Applies when: {human}" if human else ""
        except Exception:
            return ""

    def _format_constraints_text(self, field: Dict[str, Any]) -> str:
        type_name = str(field.get("type", ""))
        constraints = dict(field.get("constraints", {}) or {})

        doc_node: Dict[str, Any] = {
            "name": str(field.get("key", "")),
            "type": type_name,
            "description": str(field.get("description", "")),
            "required": bool(field.get("required", True)),
            "default": field.get("default"),
            "when": field.get("when"),
        }
        if field.get("has_default", False) is False:
            doc_node.pop("default")

        # Introspection uses normalized constraint keys; schema-doc formatter expects schema keys.
        if "min" in constraints:
            doc_node["min_value"] = constraints["min"]
        if "max" in constraints:
            doc_node["max_value"] = constraints["max"]
        if "min_length" in constraints:
            doc_node["min_length"] = constraints["min_length"]
        if "max_length" in constraints:
            doc_node["max_length"] = constraints["max_length"]
        if "enum_values" in constraints:
            doc_node["values"] = list(constraints["enum_values"])

        return format_field_constraints_for_display(
            str(field.get("key", "")),
            doc_node,
            hide_allowed_values=(type_name == "enum"),
        )

    @staticmethod
    def _format_default_text(field: Dict[str, Any]) -> str:
        if not field.get("has_default", False):
            return "-"
        return repr(field.get("default"))

    @staticmethod
    def _get_path_value(data: Dict[str, Any], dotted_path: str) -> Any:
        current: Any = data
        for part in dotted_path.split("."):
            if not isinstance(current, dict) or part not in current:
                return None
            current = current[part]
        return current

    @staticmethod
    def _format_tree_value(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (int, float, str)):
            return str(value)
        return serialize_yaml(value).strip().replace("\n", " ")

    @staticmethod
    def _path_exists(data: Dict[str, Any], dotted_path: str) -> bool:
        if not dotted_path:
            return True
        current: Any = data
        for part in dotted_path.split("."):
            if not isinstance(current, dict) or part not in current:
                return False
            current = current[part]
        return True

    def _load_config_from_path(self, path: str):
        with open(path, "r", encoding="utf-8", newline="") as handle:
            data = Schema._safe_load_yaml(handle.read(), path)
        if data is None:
            data = {}
        if not isinstance(data, dict):
            raise ValidationError(f"Config root must be a mapping/dictionary, got {type(data).__name__}")
        self.config_path = path
        self.dirty = False
        self._create_form(data)
        self._wire_validation()
        self._refresh_title_status()
        self._refresh_previews()

    def _on_load_config(self):
        path = filedialog.askopenfilename(title="Load YAML config", filetypes=[("YAML files", "*.yaml *.yml"), ("All files", "*.*")])
        if not path:
            return
        try:
            self._load_config_from_path(path)
        except (FormatError, ValidationError, FileNotFoundError) as exc:
            messagebox.showerror("Load config", f"Failed to load config: {exc}")

    def _save_to_path(self, path: str):
        if self._show_save_blocked():
            return False

        choice = messagebox.askyesnocancel(
            "Save mode",
            "Save full config with schema defaults?\n\nYes = full config\nNo = export config (default view)\nCancel = abort",
        )
        if choice is None:
            return False
        mode = SAVE_MODE_FULL if choice else SAVE_MODE_EXPORT
        payload = get_save_payload(
            mode,
            self.form_renderer.get_current_config_dict(),
            self.validation_state.data_with_default,
            schema_model=self.model,
        )
        content = serialize_yaml(payload)
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        self.config_path = path
        self.dirty = False
        self._refresh_title_status()
        return True

    def _on_save(self):
        if self._show_save_blocked():
            return
        path = self.config_path
        if not path:
            self._on_save_as()
            return
        try:
            self._save_to_path(path)
        except OSError as exc:
            messagebox.showerror("Save", f"Failed to save file: {exc}")

    def _on_save_as(self):
        if self._show_save_blocked():
            return
        path = filedialog.asksaveasfilename(
            title="Save YAML config",
            defaultextension=".yaml",
            filetypes=[("YAML files", "*.yaml *.yml"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            self._save_to_path(path)
        except OSError as exc:
            messagebox.showerror("Save As", f"Failed to save file: {exc}")

    def _on_close(self):
        if not self.dirty:
            self.root.destroy()
            return
        choice = messagebox.askyesnocancel("Unsaved changes", "You have unsaved changes. Save before closing?")
        if choice is None:
            return
        if choice:
            self._on_save()
            if self.dirty:
                return
        self.root.destroy()

    def run(self):
        self._refresh_previews()
        self.root.mainloop()


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    try:
        schema, config_data = load_schema_and_config(args.schema, args.config, args.strict)
    except (FileNotFoundError, NotADirectoryError, ValidationError, FormatError) as exc:
        message = f"Failed to start editor: {exc}"
        print(message, file=sys.stderr)
        _show_startup_error(message)
        return 1
    app = EditorApp(args.schema, args.config, args.strict, schema, config_data)
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
