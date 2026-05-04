import argparse
import sys
from pathlib import Path
from typing import Any

import tkinter as tk
from tkinter import messagebox, ttk

from readtheyaml.exceptions.format_error import FormatError
from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.schema import Schema


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


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    return build_parser().parse_args(argv)


def load_schema_and_config(
    schema_path: str,
    config_path: str | None,
    strict: bool,
) -> tuple[Schema, dict[str, Any]]:
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


def _build_editor_window(schema_path: str, config_path: str | None, strict: bool) -> tk.Tk:
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

    ttk.Label(left, text="Schema Tree (placeholder)").pack(anchor="w")
    ttk.Label(center, text="Form Editor (placeholder)").pack(anchor="w")
    ttk.Label(right, text="Validation / Output (placeholder)").pack(anchor="w")

    status_text = f"Schema: {schema_name}    Config: {config_name}    Strict: {strict}"
    status = ttk.Label(root, text=status_text, anchor="w")
    status.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))

    return root


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        load_schema_and_config(args.schema, args.config, args.strict)
    except (FileNotFoundError, NotADirectoryError, ValidationError, FormatError) as exc:
        message = f"Failed to start editor: {exc}"
        print(message, file=sys.stderr)
        _show_startup_error(message)
        return 1

    root = _build_editor_window(args.schema, args.config, args.strict)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
