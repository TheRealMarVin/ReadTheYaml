import sys

import yaml

class DataInstance:
    def __init__(self, data: dict, schema, build_now=True, strict=True):
        self.schema = schema
        self.raw = data
        self.built = None

        tata = self.schema.build_and_validate(self.raw, strict=strict)

        # if build_now:
        #     self.built = self._build()

    def _build(self):
        result = {}
        for key, field in self.schema.fields.items():
            result[key] = field.build(self.raw.get(key))
        return result

    def __getitem__(self, key):
        if self.built is None:
            self.built = self._build()
        return self.built[key]

    def dump(self, file=None):
        yaml.safe_dump(self.raw, file or sys.stdout)
