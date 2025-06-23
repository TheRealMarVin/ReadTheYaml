import sys

import yaml

class DataInstance:
    def __init__(self, data: dict, schema, strict=True):
        self.schema = schema
        self.raw = data

        self.built, self.data_with_default = self.schema.build_and_validate(self.raw, strict=strict)

    def __getitem__(self, key):
        if not key:
            raise KeyError("Empty key is not allowed.")

        keys = key.split(".")
        result = self.built
        for k in keys:
            result = result[k]
        return result

    def dump(self, file=None):
        yaml.safe_dump(self.data_with_default, file or sys.stdout)
