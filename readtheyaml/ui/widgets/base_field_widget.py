import tkinter as tk
from tkinter import ttk
from typing import Any, Optional

from readtheyaml.ui.widgets.primitives import ChangeCallback


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
        if is_invalid:
            self._input_widget.state(["invalid"])
        else:
            self._input_widget.state(["!invalid"])

    def _emit_change(self, value: Any):
        if self._on_change is not None:
            self._on_change(value)

    def set_value(self, value: Any):
        raise NotImplementedError

    def get_value(self):
        raise NotImplementedError
