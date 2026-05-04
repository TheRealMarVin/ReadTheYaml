import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Optional


ChangeCallback = Callable[[Any], None]


class ConversionResult:
    def __init__(self, value: Any, error: Optional[str] = None):
        self.value = value
        self.error = error


def normalize_str(value: str) -> ConversionResult:
    return ConversionResult(value=value)


def normalize_int(value: str) -> ConversionResult:
    text = value.strip()
    if text == "":
        return ConversionResult(value=None, error="Value is required.")
    try:
        return ConversionResult(value=int(text))
    except ValueError:
        return ConversionResult(value=None, error="Expected an integer.")


def normalize_float(value: str) -> ConversionResult:
    text = value.strip()
    if text == "":
        return ConversionResult(value=None, error="Value is required.")
    try:
        return ConversionResult(value=float(text))
    except ValueError:
        return ConversionResult(value=None, error="Expected a float.")


def normalize_bool(value: bool) -> ConversionResult:
    return ConversionResult(value=bool(value))


def normalize_enum(value: str, choices: list[str]) -> ConversionResult:
    if value not in choices:
        return ConversionResult(value=None, error="Expected one of the allowed values.")
    return ConversionResult(value=value)


class BaseFieldWidget(ttk.Frame):
    def __init__(self, parent: tk.Misc, *, label: str, description: str = "", required: bool = False, on_change: Optional[ChangeCallback] = None):
        super().__init__(parent)
        self.required = required
        self._on_change = on_change
        self._error_message = tk.StringVar(value="")

        display_label = f"{label} *" if required else label
        self.label_widget = ttk.Label(self, text=display_label)
        self.label_widget.grid(row=0, column=0, sticky="w")

        self.input_frame = ttk.Frame(self)
        self.input_frame.grid(row=1, column=0, sticky="ew")
        self.columnconfigure(0, weight=1)

        self.help_widget = ttk.Label(self, text=description or "", foreground="#666666")
        self.help_widget.grid(row=2, column=0, sticky="w")

        self.error_widget = ttk.Label(self, textvariable=self._error_message, foreground="#b00020")
        self.error_widget.grid(row=3, column=0, sticky="w")

    def mark_invalid(self, error_message: str):
        self._error_message.set(error_message)
        self._set_invalid_style(True)

    def clear_invalid(self):
        self._error_message.set("")
        self._set_invalid_style(False)

    def _set_invalid_style(self, is_invalid: bool):
        # ttk widgets support "invalid" state for style maps.
        if is_invalid:
            self._input_widget.state(["invalid"])
        else:
            self._input_widget.state(["!invalid"])

    def _emit_change(self, value: Any):
        if self._on_change is not None:
            self._on_change(value)

    def set_value(self, value: Any):
        raise NotImplementedError

    def get_value(self) -> Any:
        raise NotImplementedError


class StringFieldWidget(BaseFieldWidget):
    def __init__(self, parent: tk.Misc, **kwargs: Any):
        super().__init__(parent, **kwargs)
        self._var = tk.StringVar(value="")
        self._input_widget = ttk.Entry(self.input_frame, textvariable=self._var)
        self._input_widget.grid(row=0, column=0, sticky="ew")
        self.input_frame.columnconfigure(0, weight=1)
        self._var.trace_add("write", self._on_var_change)

    @staticmethod
    def convert(raw: str) -> ConversionResult:
        return normalize_str(raw)

    def _on_var_change(self, *_: Any):
        result = self.convert(self._var.get())
        self.clear_invalid()
        self._emit_change(result.value)

    def set_value(self, value: Any):
        self._var.set("" if value is None else str(value))

    def get_value(self) -> str:
        return self.convert(self._var.get()).value


class IntFieldWidget(BaseFieldWidget):
    def __init__(self, parent: tk.Misc, **kwargs: Any):
        super().__init__(parent, **kwargs)
        self._var = tk.StringVar(value="")
        self._input_widget = ttk.Entry(self.input_frame, textvariable=self._var)
        self._input_widget.grid(row=0, column=0, sticky="ew")
        self.input_frame.columnconfigure(0, weight=1)
        self._var.trace_add("write", self._on_var_change)

    @staticmethod
    def convert(raw: str) -> ConversionResult:
        return normalize_int(raw)

    def _on_var_change(self, *_: Any):
        result = self.convert(self._var.get())
        if result.error:
            self.mark_invalid(result.error)
            self._emit_change(None)
            return
        self.clear_invalid()
        self._emit_change(result.value)

    def set_value(self, value: Any):
        self._var.set("" if value is None else str(value))

    def get_value(self) -> Optional[int]:
        result = self.convert(self._var.get())
        return result.value


class FloatFieldWidget(BaseFieldWidget):
    def __init__(self, parent: tk.Misc, **kwargs: Any):
        super().__init__(parent, **kwargs)
        self._var = tk.StringVar(value="")
        self._input_widget = ttk.Entry(self.input_frame, textvariable=self._var)
        self._input_widget.grid(row=0, column=0, sticky="ew")
        self.input_frame.columnconfigure(0, weight=1)
        self._var.trace_add("write", self._on_var_change)

    @staticmethod
    def convert(raw: str) -> ConversionResult:
        return normalize_float(raw)

    def _on_var_change(self, *_: Any):
        result = self.convert(self._var.get())
        if result.error:
            self.mark_invalid(result.error)
            self._emit_change(None)
            return
        self.clear_invalid()
        self._emit_change(result.value)

    def set_value(self, value: Any):
        self._var.set("" if value is None else str(value))

    def get_value(self) -> Optional[float]:
        result = self.convert(self._var.get())
        return result.value


class BoolFieldWidget(BaseFieldWidget):
    def __init__(self, parent: tk.Misc, **kwargs: Any):
        super().__init__(parent, **kwargs)
        self._var = tk.BooleanVar(value=False)
        self._input_widget = ttk.Checkbutton(self.input_frame, variable=self._var, command=self._on_toggle)
        self._input_widget.grid(row=0, column=0, sticky="w")

    @staticmethod
    def convert(raw: bool) -> ConversionResult:
        return normalize_bool(raw)

    def _on_toggle(self):
        result = self.convert(self._var.get())
        self.clear_invalid()
        self._emit_change(result.value)

    def set_value(self, value: Any):
        self._var.set(bool(value))

    def get_value(self) -> bool:
        return self.convert(self._var.get()).value


class EnumFieldWidget(BaseFieldWidget):
    def __init__(self, parent: tk.Misc, *, choices: list[str], **kwargs: Any):
        super().__init__(parent, **kwargs)
        self._choices = list(choices)
        self._var = tk.StringVar(value=self._choices[0] if self._choices else "")
        self._input_widget = ttk.OptionMenu(self.input_frame, self._var, self._var.get(), *self._choices, command=self._on_select)
        self._input_widget.grid(row=0, column=0, sticky="ew")
        self.input_frame.columnconfigure(0, weight=1)

    @staticmethod
    def convert(raw: str, choices: list[str]) -> ConversionResult:
        return normalize_enum(raw, choices)

    def _on_select(self, _: str):
        result = self.convert(self._var.get(), self._choices)
        if result.error:
            self.mark_invalid(result.error)
            self._emit_change(None)
            return
        self.clear_invalid()
        self._emit_change(result.value)

    def set_value(self, value: Any):
        self._var.set("" if value is None else str(value))

    def get_value(self) -> Optional[str]:
        result = self.convert(self._var.get(), self._choices)
        return result.value
