import argparse
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from readtheyaml.exceptions.format_error import FormatError
from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.schema import Schema
from readtheyaml.ui.form_renderer import FormRenderer, evaluate_visibility_map
from readtheyaml.ui.save_helpers import SAVE_MODE_EXPORT, SAVE_MODE_FULL, can_save, get_save_payload, serialize_yaml
from readtheyaml.ui.schema_introspect import introspect_schema_dict
from readtheyaml.ui.validation import ValidationController, ValidationState, build_fix_hints


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
    _ = strict
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
        self.center = ttk.Frame(paned, padding=8)
        self.right = ttk.Frame(paned, padding=8)
        paned.add(self.left, weight=1)
        paned.add(self.center, weight=2)
        paned.add(self.right, weight=1)

        ttk.Label(self.left, text="Schema").pack(anchor="w", pady=(0, 6))
        self.tree = ttk.Treeview(self.left, columns=("kind",), show="tree headings", selectmode="browse")
        self.tree.heading("#0", text="Name", anchor="w")
        self.tree.heading("kind", text="Type", anchor="w")
        self.tree.column("#0", width=240, stretch=True)
        self.tree.column("kind", width=90, stretch=False)
        tree_scroll = ttk.Scrollbar(self.left, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self.tree.tag_configure("missing_required", foreground="#b00020")
        self.tree.tag_configure("valid_value", foreground="#1f7a1f")
        self.tree.tag_configure("inactive", foreground="#808080")

        self.toolbar = ttk.Frame(self.center)
        self.toolbar.pack(fill="x", pady=(0, 6))
        ttk.Button(self.toolbar, text="Load config", command=self._on_load_config).pack(side="left", padx=(0, 6))
        self.save_button = ttk.Button(self.toolbar, text="Save", command=self._on_save)
        self.save_button.pack(side="left", padx=(0, 6))
        self.save_as_button = ttk.Button(self.toolbar, text="Save As", command=self._on_save_as)
        self.save_as_button.pack(side="left")

        self.form_host = ttk.Frame(self.center)
        self.form_host.pack(fill="both", expand=True)

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
        self._section_path_to_item: Dict[str, str] = {}
        self.tree.delete(*self.tree.get_children())
        root_item = self.tree.insert("", "end", text=self.model.get("name") or "<root>", values=("section",), open=True)
        self._tree_item_to_path[root_item] = ("section", "")
        self._section_path_to_item[""] = root_item
        self._add_tree_nodes(root_item, self.model)

    def _add_tree_nodes(self, parent_item: str, section_model: Dict[str, Any]):
        section_path = self._normalize_path(section_model.get("path", ""))
        for field in section_model.get("fields", []):
            field_path = f"{section_path}.{field['key']}" if section_path else field["key"]
            type_name = field.get("type", "")
            node = self.tree.insert(parent_item, "end", text=field["key"], values=(type_name,))
            self._tree_item_to_path[node] = ("field", field_path)
            self._field_path_to_item[field_path] = node
            self._field_required[field_path] = bool(field.get("required", True))

        for subsection in section_model.get("subsections", []):
            subsection_path = self._normalize_path(subsection.get("path", ""))
            label = subsection_path.split(".")[-1] if subsection_path else (subsection.get("name") or "<root>")
            node = self.tree.insert(parent_item, "end", text=label, values=("section",), open=False)
            self._tree_item_to_path[node] = ("section", subsection_path)
            self._section_path_to_item[subsection_path] = node
            self._add_tree_nodes(node, subsection)

    def _on_tree_select(self, _: tk.Event):
        selection = self.tree.selection()
        if not selection:
            return
        item = selection[0]
        mapping = self._tree_item_to_path.get(item)
        if mapping is None:
            return
        node_kind, path = mapping
        if node_kind == "section":
            self.form_renderer.reveal_section(path)
            return
        self.form_renderer.focus_field(path)

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
