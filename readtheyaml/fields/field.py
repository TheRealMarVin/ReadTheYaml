class Field:
    def __init__(self, name, required=True, default=None, description="Default Definition", **kwargs):
        self.name = name
        self.required = required
        self.default = default
        self.description = description

    def validate(self, value):
        raise NotImplementedError("Each field must implement its own validate method.")
