import tkinter as tk
from tkinter import ttk
from typing import Any

from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.fields.base.bool_field import BoolField
from readtheyaml.ui.widgets.primitives import ConversionResult
from readtheyaml.ui.widgets.base_field_widget import BaseFieldWidget


class BoolFieldWidget(BaseFieldWidget):
    def __init__(self, parent: tk.Misc, **kwargs: Any):
        super().__init__(parent, **kwargs)
        self._var = tk.BooleanVar(value=False)
        self._input_widget = ttk.Checkbutton(self.input_frame, variable=self._var, command=self._on_toggle)
        self._input_widget.grid(row=0, column=0, sticky="w")

    @staticmethod
    def convert(raw: bool):
        try:
            field = BoolField(name="__ui__", description="", required=True, ignore_post=True)
            return ConversionResult(value=field.validate_and_build(raw))
        except ValidationError as exc:
            return ConversionResult(value=None, error=str(exc).removeprefix("Field '__ui__': "))

    def _on_toggle(self):
        result = self.convert(self._var.get())
        self.clear_invalid()
        self._emit_change(result.value)

    def set_value(self, value: Any):
        self._var.set(bool(value))

    def get_value(self):
        return self.convert(self._var.get()).value
