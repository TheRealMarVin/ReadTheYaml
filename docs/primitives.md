# Primitive Types

## `any`

Example schema:

```yaml
payload:
  type: any
  required: false
  default: {}
  description: extra arbitrary values
```

Example config:

```yaml
payload:
  retries: 3
  tags: [a, b]
```

Supports:
- Accepts any runtime value without transformation.
- Works with optional fields only when an explicit `default` is provided.

Limitations:
- Optional `any` without explicit default is rejected.

## `bool`

Example schema:

```yaml
enabled:
  type: bool
  description: feature flag
```

Example config:

```yaml
enabled: "true"
```

Supports:
- Native booleans.
- Case-insensitive string inputs: `"true"` and `"false"`.

Limitations:
- Rejects `null`, `"null"`, `"none"`, and empty strings.
- Rejects non-boolean numeric values.

## `enum`

Example schema:

```yaml
mode:
  type: enum
  values: [auto, manual]
  description: operating mode
```

Example config:

```yaml
mode: auto
```

Supports:
- Membership validation against `values` list/tuple.

Limitations:
- `values` is mandatory and must be non-empty.
- Matching is exact (case-sensitive, type-sensitive).

## `None`

Example schema:

```yaml
deprecated:
  type: None
  required: false
  default: null
  description: reserved field
```

Example config:

```yaml
deprecated: null
```

Supports:
- YAML null / Python `None`.
- String values `"none"` and `"null"` (case-insensitive), normalized to `None`.

Limitations:
- Any other input is rejected.

## `int` and `float`

Example schema:

```yaml
retries:
  type: int
  min_value: 0
  max_value: 10
  description: retry count

threshold:
  type: float
  min_value: 0.0
  max_value: 1.0
  description: confidence threshold
```

Example config:

```yaml
retries: "3"
threshold: "0.55"
```

Supports:
- Type conversion from compatible scalar inputs (including numeric strings).
- Optional range validation via `min_value`, `max_value`, or `value_range`.

Limitations:
- Boolean-like inputs (`true`/`false`) are rejected.
- `int` rejects non-integral floats.
- Range metadata with wrong types is rejected at schema build time.

## `str`

Example schema:

```yaml
nickname:
  type: str
  required: false
  default: ""
  min_length: 0
  max_length: 30
  description: display name
```

Example config:

```yaml
nickname: "alice"
```

Supports:
- Strict string validation by default.
- Optional conversion via `cast_to_string=True`.
- Length bounds via `min_length` and `max_length`.

Limitations:
- Without `cast_to_string`, non-string values are rejected.
- `min_length < 0` or `max_length < min_length` is rejected at schema build time.
