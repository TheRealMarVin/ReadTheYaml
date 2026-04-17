# Composite Types

## `list[T]`

Example schema:

```yaml
ports:
  type: list[int]
  min_length: 1
  max_length: 4
  description: allowed ports
```

Example config:

```yaml
ports: [8080, 8081]
```

Supports:
- List item validation using nested field type `T`.
- Length constraints via `min_length`, `max_length`, `length_range`.
- Returns validated/built items.

Limitations:
- Only accepts Python/YAML list input.
- Fails fast with index-specific error when one item is invalid.

## `tuple[T1, T2, ...]`

Example schema:

```yaml
coordinates:
  type: tuple[float, float]
  description: x,y position
```

Example config:

```yaml
coordinates: "(12.5, 42.0)"
```

Supports:
- Fixed-arity tuples with per-slot type validation.
- Tuple literal strings such as `"(1, 'x')"` are parsed and accepted.

Limitations:
- YAML list input is rejected (must be tuple or tuple-string form).
- Arity must match exactly.
- Validation does not rebuild each element into normalized output; it validates and returns the tuple value.

## `union[A, B]` or `A | B`

Example schema:

```yaml
id_or_name:
  type: int | str
  description: identifier can be numeric or textual
```

Example config:

```yaml
id_or_name: 101
```

Invalid config:

```yaml
id_or_name: false
```

Supports:
- First-match validation across ordered options.
- Complex options (list/tuple/object) are supported.
- Rich error output when no option matches.

Limitations:
- Duplicate option field classes are rejected (even if parameterized differently).
- `StringField(cast_to_string=True)` is explicitly forbidden in unions.
- Option order matters when multiple options could match.
