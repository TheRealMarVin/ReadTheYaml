# Schema lifecycle

This page describes how `ReadTheYaml` turns schema YAML + input data into validated Python data.

## 1) `Schema.from_yaml(...)`: load + base directory resolution

`Schema.from_yaml(schema_file, base_schema_dir=None)` does three things before any parsing:

1. Verifies `schema_file` exists (`FileNotFoundError` if not).
2. Resolves `base_schema_dir`:
   - uses the explicit argument when provided;
   - otherwise defaults to the directory containing `schema_file`.
3. Verifies `base_schema_dir` exists (`NotADirectoryError` if not), loads YAML with `yaml.safe_load`, then delegates to `Schema._from_dict(data, base_schema_dir)`.

That base directory is later used by `$ref` resolution in `_resolve_ref`.

## 2) `Schema._from_dict(...)`: parsing into fields and subsections

`Schema._from_dict(data, base_schema_dir)` recursively walks a Python dictionary and splits entries into either **fields** or **subsections**:

- **Field**: dictionary contains `type`, so it is built by `FIELD_FACTORY.create_field(...)`.
- **Referenced subsection**: dictionary contains `$ref`; referenced YAML is loaded and merged with local overrides, then recursively parsed.
- **Nested subsection**: dictionary has neither `type` nor `$ref`; it is recursively parsed as a nested `Schema`.

Additional behavior:

- Reserved field names are rejected with `FormatError`.
- Field-construction failures are wrapped as `ValidationError` (`Failed to build field ...`).
- Section metadata (`name`, `description`, `required`, `default`) is captured on each `Schema` instance.

## 3) `Schema.build_and_validate(...)` behavior

`Schema.build_and_validate(data, strict=True)` returns a tuple:

- `built_data`: validated/coerced values used by runtime access.
- `data_with_default`: input-like structure with injected defaults for dumping/export.

### Required fields

For each field:

- if present in input → validate/build via `field.validate_and_build(...)`;
- if missing and `required=True` → `ValidationError("Missing required field ...")`;
- if missing and optional → use field default.

### Default injection

Defaults are injected into both:

- `built_data[field_name]`, and
- `data_with_default[field_name]`.

For optional subsections:

- if subsection has explicit section-level default (`has_default=True`) that value is copied directly;
- otherwise the subsection is recursively built from `{}`, allowing child field defaults to be populated.

### Nested subsection validation

Each declared subsection is recursively validated through `subsection.build_and_validate(...)`.

- Missing required subsection raises `ValidationError("Missing required section ...")`.
- Nested errors bubble up from child validations.

### Strict vs non-strict unknown key handling

Allowed keys are `fields ∪ subsections` for the current section.

- `strict=True` (default): any extra keys cause `ValidationError("Unexpected key(s) ...")`.
- `strict=False`: extra keys are preserved in `built_data` unchanged.

## 4) `DataInstance` role after validation

`DataInstance(data, schema, strict=True)` is a thin runtime wrapper around schema validation:

- stores `schema` and raw input as `raw`;
- calls `schema.build_and_validate(...)` once at construction;
- exposes:
  - `built` (validated runtime data),
  - `data_with_default` (export-ready data including defaults).

Access patterns from `readtheyaml/data_instance.py` and `tests/test_data_instance.py`:

- `instance["key"]` for top-level access;
- dotted-path lookup `instance["db.host"]` for nested dictionaries;
- empty key raises `KeyError`;
- `dump()` emits YAML from `data_with_default`.

Tests also confirm:

- strict mode rejects unknown keys;
- non-strict mode preserves unknown keys;
- nested defaults are materialized and accessible.

---

## Minimal runnable example using `examples/schema.yaml` and `examples/valid_config.yaml`

> This repository's `examples/schema.yaml` uses `fields:`/`subsections:` wrappers, while `Schema._from_dict(...)` expects fields/subsections at the same mapping level. The example below normalizes the file into the parser shape, then validates `examples/valid_config.yaml`.

```python
from pathlib import Path
import yaml

from readtheyaml.data_instance import DataInstance
from readtheyaml.schema import Schema


def normalize_example_schema(node: dict) -> dict:
    """Convert examples/schema.yaml wrapper format into Schema._from_dict format."""
    out = {}

    for k in ("name", "description", "required", "default"):
        if k in node:
            out[k] = node[k]

    # Lift fields into the current object
    for field_name, field_spec in node.get("fields", {}).items():
        spec = dict(field_spec)
        spec.pop("range", None)  # NumericalField currently rejects `range`
        out[field_name] = spec

    # Lift subsections into the current object (recursively)
    for section_name, section_spec in node.get("subsections", {}).items():
        out[section_name] = normalize_example_schema(section_spec)

    return out


schema_path = Path("examples/schema.yaml")
config_path = Path("examples/valid_config.yaml")

schema_yaml = yaml.safe_load(schema_path.read_text())
schema_dict = normalize_example_schema(schema_yaml)
schema_dict.pop("app_config", None)  # valid_config uses app_config as plain string

schema = Schema._from_dict(schema_dict, base_schema_dir=schema_path.parent)

config = yaml.safe_load(config_path.read_text())
config.pop("app_config", None)

instance = DataInstance(config, schema, strict=False)

print(instance["network.server.host"])  # 127.0.0.1
print(instance["network.server.port"])  # 8080 (default injected)
print(instance["logging.level"])        # info (default injected)
print("test" in instance.built)          # True (extra key preserved in non-strict mode)
```

Run from repository root:

```bash
PYTHONPATH=. python your_script.py
```
