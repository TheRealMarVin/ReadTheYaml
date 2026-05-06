import tkinter as tk
from tkinter import ttk
from typing import Any

from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.fields.base.numerical_field import NumericalField
from readtheyaml.ui.widgets.primitives import ConversionResult, INVALID_INPUT
from readtheyaml.ui.widgets.base_field_widget import BaseFieldWidget


class FloatFieldWidget(BaseFieldWidget):
    def __init__(self, parent: tk.Misc, **kwargs: Any):
        super().__init__(parent, **kwargs)
        self._var = tk.StringVar(value="")
        self._input_widget = ttk.Entry(self.input_frame, textvariable=self._var)
        self._input_widget.grid(row=0, column=0, sticky="ew")
        self.input_frame.columnconfigure(0, weight=1)
        self._var.trace_add("write", self._on_var_change)

    @staticmethod
    def convert(raw: str, required: bool = False):
        text = raw.strip()
        if text == "":
            if required:
                return ConversionResult(value=None, error="Value is required.")
            return ConversionResult(value=None)
        try:
            field = NumericalField(name="__ui__", description="", required=required, value_type=float, ignore_post=True)
            return ConversionResult(value=field.validate_and_build(text))
        except ValidationError as exc:
            return ConversionResult(value=None, error=str(exc).removeprefix("Field '__ui__': "))

    def _on_var_change(self, *_: Any):
        result = self.convert(self._var.get(), required=self.required)
        if result.error:
            self.mark_invalid(result.error)
            self._emit_change(INVALID_INPUT)
            return
        self.clear_invalid()
        self._emit_change(result.value)

    def set_value(self, value: Any):
        self._var.set("" if value is None else str(value))

    def get_value(self):
        result = self.convert(self._var.get(), required=self.required)
        return result.value
