from typing import Any, Callable, Optional

ChangeCallback = Callable[[Any], None]
INVALID_INPUT = object()


class ConversionResult:
    def __init__(self, value: Any, error: Optional[str] = None):
        self.value = value
        self.error = error
