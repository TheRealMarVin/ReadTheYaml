import tkinter as tk
from tkinter import ttk
from typing import Any

from readtheyaml.ui.widgets.base_field_widget import BaseFieldWidget
from readtheyaml.ui.widgets.primitives import ConversionResult


class NoneFieldWidget(BaseFieldWidget):
    def __init__(self, parent: tk.Misc, **kwargs: Any):
        super().__init__(parent, **kwargs)
        self._input_widget = ttk.Label(self.input_frame, text="null (read-only)")
        self._input_widget.grid(row=0, column=0, sticky="w")

    @staticmethod
    def convert(_: Any = None):
        return ConversionResult(value=None)

    def set_value(self, value: Any):
        _ = value

    def get_value(self):
        return None
