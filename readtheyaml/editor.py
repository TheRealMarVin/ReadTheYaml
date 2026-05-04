import argparse
import sys
from pathlib import Path
from typing import Any, Optional, Tuple, Dict

import tkinter as tk
from tkinter import messagebox, ttk
import yaml

from readtheyaml.exceptions.format_error import FormatError
from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.schema import Schema
from readtheyaml.ui.form_renderer import FormRenderer
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
    parser.add_argument(
        "--strict",
        type=_parse_bool,
        default=True,
        help="Strict validation mode (true|false, default: true)",
    )
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

    # Editor startup should allow partial/incomplete configs so users can fix them in the UI.
    # Full validation is expected to run during explicit validation actions inside the editor.
    return schema, config_data


def _show_startup_error(message: str) -> None:
    try:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("ReadTheYAML Editor", message)
        root.destroy()
    except tk.TclError:
        pass


def _build_editor_window(schema_path: str, config_path: Optional[str], strict: bool, schema: Schema, config_data: Dict[str, Any]) -> tk.Tk:
    schema_name = Path(schema_path).name
    config_name = Path(config_path).name if config_path else "<none>"

    root = tk.Tk()
    root.title(f"ReadTheYAML Editor - schema: {schema_name} | config: {config_name}")
    root.geometry("1100x700")

    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    paned = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
    paned.grid(row=0, column=0, sticky="nsew")

    left = ttk.Frame(paned, padding=8)
    center = ttk.Frame(paned, padding=8)
    right = ttk.Frame(paned, padding=8)
    paned.add(left, weight=1)
    paned.add(center, weight=2)
    paned.add(right, weight=1)

    model = introspect_schema_dict(schema)

    ttk.Label(left, text="Schema Tree (placeholder)").pack(anchor="w")
    ttk.Label(left, text=f"Fields: {len(model.get('fields', []))}").pack(anchor="w")

    form_renderer = FormRenderer(center, model, config_data, strict=strict)
    form_renderer.pack(fill="both", expand=True)

    badge = tk.Label(right, text="PENDING", bg="#888888", fg="white", padx=8, pady=4)
    badge.pack(anchor="w", pady=(0, 8))

    error_label = ttk.Label(right, text="Global Errors", anchor="w")
    error_label.pack(fill="x")
    error_text = tk.Text(right, height=8, wrap="word")
    error_text.pack(fill="x", pady=(0, 8))
    hint_label = ttk.Label(right, text="How to fix", anchor="w")
    hint_label.pack(fill="x")
    hint_text = tk.Text(right, height=6, wrap="word")
    hint_text.pack(fill="x", pady=(0, 8))
    output_label = ttk.Label(right, text="Built Output", anchor="w")
    output_label.pack(fill="x")
    output_text = tk.Text(right, height=10, wrap="word")
    output_text.pack(fill="both", expand=True)

    def set_text(widget: tk.Text, value: str):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", value)
        widget.configure(state="disabled")

    def on_validation_state(state: ValidationState):
        form_renderer.apply_field_errors(state.field_errors)
        if state.is_valid:
            badge.configure(text="VALID", bg="#1f7a1f")
            set_text(error_text, "")
            set_text(hint_text, "")
            built_output = yaml.safe_dump(state.built_output, sort_keys=False)
            with_default = yaml.safe_dump(state.data_with_default, sort_keys=False)
            set_text(output_text, f"built_output:\n{built_output}\n---\ndata_with_default:\n{with_default}")
            return

        badge.configure(text="INVALID", bg="#a32121")
        errors = list(state.global_errors)
        for path, msg in sorted(state.field_errors.items()):
            errors.append(f"{path}: {msg}")
        set_text(error_text, "\n".join(errors))
        hints = build_fix_hints(state.field_errors, state.global_errors)
        set_text(hint_text, "\n".join(hints))
        set_text(output_text, "")

    controller = ValidationController(
        schema=schema,
        strict=strict,
        schedule_callback=lambda delay, cb: root.after(delay, cb),
        cancel_callback=lambda token: root.after_cancel(token),
        state_callback=on_validation_state,
        debounce_ms=300,
    )

    def on_form_change(_: Dict[str, Any]):
        controller.request_validation(form_renderer.get_current_config_dict())

    form_renderer.set_on_change(on_form_change)
    controller.request_validation(form_renderer.get_current_config_dict())

    status_text = f"Schema: {schema_name}    Config: {config_name}    Strict: {strict}"
    status = ttk.Label(root, text=status_text, anchor="w")
    status.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))

    return root


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    try:
        schema, config_data = load_schema_and_config(args.schema, args.config, args.strict)
    except (FileNotFoundError, NotADirectoryError, ValidationError, FormatError) as exc:
        message = f"Failed to start editor: {exc}"
        print(message, file=sys.stderr)
        _show_startup_error(message)
        return 1

    root = _build_editor_window(args.schema, args.config, args.strict, schema, config_data)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
