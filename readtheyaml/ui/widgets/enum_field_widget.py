import tkinter as tk
from tkinter import ttk
from typing import Any

from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.fields.base.enum_field import EnumField
from readtheyaml.ui.widgets.primitives import ConversionResult
from readtheyaml.ui.widgets.base_field_widget import BaseFieldWidget


class EnumFieldWidget(BaseFieldWidget):
    def __init__(self, parent: tk.Misc, *, choices: list[str], **kwargs: Any):
        super().__init__(parent, **kwargs)
        self._choices = list(choices)
        self._var = tk.StringVar(value=self._choices[0] if self._choices else "")
        self._input_widget = ttk.OptionMenu(self.input_frame, self._var, self._var.get(), *self._choices, command=self._on_select)
        self._input_widget.grid(row=0, column=0, sticky="ew")
        self.input_frame.columnconfigure(0, weight=1)

    @staticmethod
    def convert(raw: str, choices: list[str]):
        try:
            field = EnumField(name="__ui__", description="", required=True, values=list(choices), ignore_post=True)
            return ConversionResult(value=field.validate_and_build(raw))
        except ValidationError as exc:
            return ConversionResult(value=None, error=str(exc).removeprefix("Field '__ui__': "))

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

    def get_value(self):
        result = self.convert(self._var.get(), self._choices)
        return result.value
