# Schema and DataInstance

## `Schema`

Supports:
- Build schema from dict or YAML (`from_yaml`).
- Field and nested subsection validation.
- Conditional inclusion with `when` on fields and subsections.
- Strict mode (`strict=True`) for unknown-key rejection.
- Non-strict mode passthrough for unknown keys.
- Local and HTTP `$ref` loading.
- Optional sections with explicit defaults.

Limitations:
- Input data for validation must be a dictionary at each section.
- Reserved keywords cannot be used as field names.
- Optional fields usually require valid defaults (enforced per field class).
- HTTP `$ref` uses `requests` at runtime; missing dependency or network failure will fail resolution.

### `when` behavior summary

- `when` is evaluated before validating the target field/subsection.
- If condition is false:
  - the field/subsection is skipped
  - it is omitted from `built`
  - it is removed from `data_with_default` if present
- If condition is true, normal required/default/type validation applies.
- Conditions can reference nested paths using dot notation (for example `feature.flags.beta`).

See [conditions.md](conditions.md) for full operator and combinator details.

## `DataInstance`

Supports:
- Wraps schema validation and stores:
  - `built`: validated output
  - `data_with_default`: original structure plus injected defaults
- Dot-path access with `instance["a.b.c"]`.
- YAML dump of data-with-defaults.

Limitations:
- Empty key access is rejected.
- Dot-path lookup assumes nested dict/object shape and raises `KeyError` on missing segments.
