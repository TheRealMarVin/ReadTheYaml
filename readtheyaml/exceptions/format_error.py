class FormatError(Exception):
    def __init__(self, message: str, path: str = ""):
        self.message = message
        self.path = path
        super().__init__(self.full_message)

    @property
    def full_message(self) -> str:
        if self.path:
            return f"[{self.path}] {self.message}"
        return self.message

    def __str__(self) -> str:
        return self.full_message
