class Field:
    def __init__(self, required=True, default=None):
        self.required = required
        self.default = default

    def validate(self, value):
        raise NotImplementedError("Each field must implement its own validate method.")
