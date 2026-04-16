# Schema references and subsections

This page documents how `ReadTheYaml` handles `$ref`, nested subsections, and optional subsection defaults, using `examples/schema_ref.yaml` and `examples/shared/*.yaml` as canonical examples.

## 1) `$ref` resolution in `Schema._resolve_ref`

`Schema._resolve_ref(ref, base_dir)` supports two resolution paths:

### Local file references (relative to `base_schema_dir`)

For non-URL refs, the code resolves paths like this:

1. `target = (base_dir / ref).resolve()`
2. Checks `target.exists()` and raises `FileNotFoundError` if missing.
3. Loads YAML from that resolved file with `yaml.safe_load(...)`.

`base_dir` comes from `Schema._from_dict(..., base_schema_dir=...)`, and that in turn comes from `Schema.from_yaml(schema_file, base_schema_dir=None)`. If `base_schema_dir` is omitted, `from_yaml` sets it to the directory containing the schema file.

So in `examples/schema_ref.yaml`, these entries:

- `network.server.$ref: ./shared/server.yaml`
- `logging.$ref: ./shared/logging.yaml`
- `test.$ref: ./shared/test.yaml`

are resolved relative to `examples/` when loading `examples/schema_ref.yaml` through `Schema.from_yaml(...)`.

### Remote URL references (as currently implemented)

If `ref` starts with `https://`, `_resolve_ref` imports `requests`, performs `requests.get(ref, timeout=10)`, then calls `raise_for_status()` and parses the returned text as YAML.

Important implementation note: the condition currently checks `ref.startswith("https://") or ref.startswith("https://")` (same predicate twice). That means:

- `https://...` refs are treated as remote;
- `http://...` refs are **not** treated as remote and instead go through local path resolution.

This section intentionally describes behavior **as implemented**, not as one might expect ideally.

## 2) Merge semantics in `_from_dict` for `$ref`

When `_from_dict` encounters a mapping with `$ref`, it does:

1. `ref_dict = cls._resolve_ref(ref_path, base_schema_dir)`
2. `full_section_data = ref_dict.copy()`
3. `full_section_data.update({k: v for k, v in value.items() if k != "$ref"})`
4. Recursively parses `full_section_data` as the subsection schema.

This means referenced content is copied first, then local inline keys override same-named keys from the referenced file.

### Example from `examples/schema_ref.yaml`

`logging` references `examples/shared/logging.yaml` and sets `required: false` inline:

```yaml
logging:
  $ref: ./shared/logging.yaml
  required: false
```

After merge, the subsection includes all referenced logging fields (`level`, `to_file`, `filepath`) plus inline overrides (here, section-level `required: false`).

The same pattern applies to `network.server` and `test` sections when they are declared via `$ref`.

## 3) How `_from_dict` distinguishes subsection/field/reference shapes

For each `key: value` where `value` is a dictionary, `_from_dict` uses this precedence:

1. **Field declaration**: if `"type" in value`
   - Built as a field via `FIELD_FACTORY.create_field(...)`.
   - Example: in `examples/shared/server.yaml`, `host` and `port` both have `type`, so they become fields.

2. **Referenced subsection**: else if `"$ref" in value`
   - Reference is resolved and merged, then recursively parsed as a subsection.
   - Example: in `examples/schema_ref.yaml`, `network.server`, `logging`, and `test` all use `$ref`.

3. **Nested subsection dict**: else (dict with neither `type` nor `$ref`)
   - Parsed recursively as an inline subsection.
   - Example: in `examples/schema_ref.yaml`, `network` itself is this shape (`description`, `required`, and nested key `server`).

In short:

- no `type`, no `$ref` → inline/nested subsection;
- `type` present → field;
- `$ref` present (and no `type`) → referenced subsection.

## 4) Optional subsection behavior and `default: None`

`Schema.build_and_validate(...)` handles missing optional subsections in two branches:

1. If subsection has an explicit section-level default (`has_default=True`), it injects that default directly.
2. Otherwise, it recursively builds the subsection from `{}`, which lets child defaults populate.

### Behavior when optional subsection is missing

- **No section-level default**: missing subsection expands child defaults.
- **Section-level `default: None`**: missing subsection stays `None` and child defaults are not expanded.

This matches `tests/test_schema.py`:

- `test_schema_optional_subsection_not_provided` expects `{"enabled": False}` for the missing optional section (child default expansion).
- `test_schema_optional_subsection_with_none_default_not_expanded` expects `None` for the whole section when section-level default is explicitly `None`.

So `default: None` at subsection level is the opt-out switch for automatic child-default expansion.
