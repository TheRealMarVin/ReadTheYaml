import importlib
import inspect
import tkinter as tk
from tkinter import ttk
from typing import Any, get_type_hints

from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.fields.field_factory import FIELD_FACTORY
from readtheyaml.ui.widgets.base_field_widget import BaseFieldWidget
from readtheyaml.ui.widgets.primitives import INVALID_INPUT


class ObjectFieldWidget(BaseFieldWidget):
    def __init__(self, parent: tk.Misc, *, parameters: list[dict[str, Any]] | None = None, class_path: str | None = None, **kwargs: Any):
        super().__init__(parent, **kwargs)
        self._parameters = list(parameters or [])
        self._class_path = class_path
        self._values: dict[str, Any] = {}
        if not self._parameters and self._class_path:
            self._parameters = self.inspect_constructor_parameters(self._class_path)

        if class_path:
            self._input_widget = ttk.Label(self.input_frame, text=f"Class: {class_path}")
            self._input_widget.grid(row=0, column=0, sticky="w")
        else:
            self._input_widget = ttk.Label(self.input_frame, text="Class path not fixed")
            self._input_widget.grid(row=0, column=0, sticky="w")

        self._tree = ttk.Treeview(self.input_frame, columns=("type", "value"), show="tree headings", height=max(3, min(8, len(self._parameters) + 1)))
        self._tree.heading("#0", text="Parameter", anchor="w")
        self._tree.heading("type", text="Type", anchor="w")
        self._tree.heading("value", text="Value", anchor="w")
        self._tree.column("#0", width=160, stretch=True)
        self._tree.column("type", width=130, stretch=False)
        self._tree.column("value", width=180, stretch=True)
        self._tree.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        self.input_frame.columnconfigure(0, weight=1)

        self._editor = ttk.Frame(self.input_frame)
        self._editor.grid(row=2, column=0, sticky="ew", pady=(6, 0))
        self._editor.columnconfigure(1, weight=1)

        ttk.Label(self._editor, text="Selected value").grid(row=0, column=0, sticky="w")
        self._selected_var = tk.StringVar(value="")
        self._selected_entry = ttk.Entry(self._editor, textvariable=self._selected_var)
        self._selected_entry.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        self._selected_var.trace_add("write", self._on_selected_value_change)
        self._selected_param_name: str | None = None

        self._build_rows()
        self._tree.bind("<<TreeviewSelect>>", self._on_select_row)

    def _build_rows(self):
        for item in self._tree.get_children():
            self._tree.delete(item)
        for param in self._parameters:
            name = str(param.get("name", ""))
            type_name = str(param.get("type", "any"))
            required = bool(param.get("required", True))
            label = f"{name} *" if required else name
            value = self._values.get(name, param.get("default"))
            value_text = "" if value is None else str(value)
            self._tree.insert("", "end", iid=name, text=label, values=(type_name, value_text))

    def _on_select_row(self, *_: Any):
        selected = self._tree.selection()
        if not selected:
            self._selected_param_name = None
            self._selected_var.set("")
            return
        self._selected_param_name = selected[0]
        value = self._values.get(self._selected_param_name, None)
        self._selected_var.set("" if value is None else str(value))

    def _on_selected_value_change(self, *_: Any):
        if not self._selected_param_name:
            return
        param = next((p for p in self._parameters if p.get("name") == self._selected_param_name), None)
        if param is None:
            return

        raw = self._selected_var.get()
        required = bool(param.get("required", True))
        type_name = str(param.get("type", "any"))
        if raw.strip() == "":
            if required:
                self.mark_invalid(f"Parameter '{self._selected_param_name}' is required.")
                self._emit_change(INVALID_INPUT)
                return
            self._values.pop(self._selected_param_name, None)
            self._tree.set(self._selected_param_name, "value", "")
            self.clear_invalid()
            self._emit_change(self.get_value())
            return

        try:
            validator = FIELD_FACTORY.create_field(
                type_name,
                "__ui_object__",
                description="",
                required=required,
                ignore_post=True,
            )
            converted = validator.validate_and_build(raw)
        except (ValidationError, ValueError, TypeError) as exc:
            self.mark_invalid(str(exc).replace("Field '__ui_object__': ", "").strip())
            self._emit_change(INVALID_INPUT)
            return

        self._values[self._selected_param_name] = converted
        self._tree.set(self._selected_param_name, "value", str(converted))
        self.clear_invalid()
        self._emit_change(self.get_value())

    def set_value(self, value: Any):
        if isinstance(value, dict):
            self._values = {str(k): v for k, v in value.items()}
        else:
            self._values = {}
        self._build_rows()

    def get_value(self):
        built: dict[str, Any] = {}
        for param in self._parameters:
            name = str(param.get("name", ""))
            required = bool(param.get("required", True))
            if name in self._values:
                built[name] = self._values[name]
            elif required:
                return INVALID_INPUT
        return built

    @staticmethod
    def inspect_constructor_parameters(class_path: str) -> list[dict[str, Any]]:
        module_path, _, class_name = class_path.rpartition(".")
        if not module_path:
            return []
        try:
            module = importlib.import_module(module_path)
            cls = getattr(module, class_name)
            signature, signature_source = ObjectFieldWidget._get_best_constructor_signature(cls)
            if signature is None:
                return []

            hints: dict[str, Any] = {}
            try:
                hints.update(get_type_hints(signature_source))
            except Exception:
                pass

            for hint_source_name in ("__init__", "__new__"):
                hint_source = getattr(cls, hint_source_name, None)
                if hint_source is None:
                    continue
                try:
                    hints.update(get_type_hints(hint_source))
                except Exception:
                    pass
        except Exception:
            return []

        parameters: list[dict[str, Any]] = []
        for name, parameter in signature.parameters.items():
            if name in {"self", "cls"}:
                continue
            if parameter.kind in {inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD}:
                continue

            hint = parameter.annotation
            if hint is inspect.Signature.empty:
                hint = hints.get(name)
            type_name = ObjectFieldWidget._type_name(hint) if hint is not None else "any"
            has_default = parameter.default is not inspect.Parameter.empty
            parameters.append(
                {
                    "name": name,
                    "required": not has_default,
                    "has_default": has_default,
                    "default": parameter.default if has_default else None,
                    "type": type_name,
                }
            )
        return parameters

    @staticmethod
    def _is_generic_signature(signature: inspect.Signature) -> bool:
        parameters = [
            parameter
            for parameter in signature.parameters.values()
            if parameter.name not in {"self", "cls"}
        ]
        if not parameters:
            return False
        return all(
            parameter.kind in {inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD}
            for parameter in parameters
        )

    @staticmethod
    def _get_best_constructor_signature(cls: type[Any]) -> tuple[inspect.Signature | None, Any]:
        candidates = [cls, getattr(cls, "__init__", None), getattr(cls, "__new__", None)]
        fallback: tuple[inspect.Signature, Any] | None = None

        for candidate in candidates:
            if candidate is None:
                continue
            try:
                signature = inspect.signature(candidate)
            except (TypeError, ValueError):
                continue

            if not ObjectFieldWidget._is_generic_signature(signature):
                return signature, candidate
            if fallback is None:
                fallback = (signature, candidate)

        if fallback is not None:
            return fallback
        return None, None

    @staticmethod
    def _type_name(type_hint: Any) -> str:
        if type_hint is None:
            return "any"
        if type_hint is inspect.Signature.empty:
            return "any"
        if type_hint is type(None):
            return "none"
        origin = getattr(type_hint, "__origin__", None)
        args = getattr(type_hint, "__args__", ())
        if origin is None:
            if hasattr(type_hint, "__name__"):
                name = str(type_hint.__name__)
                if name == "str":
                    return "str"
                if name == "int":
                    return "int"
                if name == "float":
                    return "float"
                if name == "bool":
                    return "bool"
            return "any"
        origin_name = getattr(origin, "__name__", str(origin))
        if origin_name == "Union":
            joined = ", ".join(ObjectFieldWidget._type_name(arg) for arg in args)
            return f"union({joined})"
        if origin_name in {"list", "tuple"} and args:
            joined = ", ".join(ObjectFieldWidget._type_name(arg) for arg in args)
            return f"{origin_name}({joined})"
        return "any"
