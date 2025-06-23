import sys

import yaml

class DataInstance:
    def __init__(self, data: dict, schema, strict=True):
        self.schema = schema
        self.raw = data

        self.built, self.data_with_default = self.schema.build_and_validate(self.raw, strict=strict)

    def __getitem__(self, key):
        if self.built is None:
            self.built = self._build()
        return self.built[key]

    def dump(self, file=None):
        yaml.safe_dump(self.data_with_default, file or sys.stdout)
