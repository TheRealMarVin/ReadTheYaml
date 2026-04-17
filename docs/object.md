# Object Type

## `object[package.module.ClassName]` or dotted class path

### Fixed class example

Schema:

```yaml
owner:
  type: object[myapp.models.User]
  description: fixed object type
```

Config:

```yaml
owner:
  name: Alice
  age: 30
```

### Base class with derived `_type_` example

Schema:

```yaml
pet:
  type: object[myapp.models.Animal]
  description: base class with optional derived _type_
```

Config:

```yaml
pet:
  _type_: myapp.models.Dog
  name: Rex
  breed: Labrador
```

### Fully dynamic object example

Schema:

```yaml
dynamic_target:
  type: object
  description: dynamic object, _type_ is required
```

Config:

```yaml
dynamic_target:
  _type_: myapp.models.Server
  host: localhost
  port: 8080
```

Invalid config (missing `_type_`):

```yaml
dynamic_target:
  host: localhost
  port: 8080
```

Supports:
- Constructor-driven validation from type hints.
- Untyped constructor args fallback to `any`.
- Optional subclass override via `_type_` sentinel when a base class is configured.
- Dynamic object resolution when no fixed `class_path` is set (requires `_type_` in data).
- Direct scalar construction for fixed class paths when value is not a mapping.

Limitations:
- Non-dict input for dynamic object mode is rejected.
- Unknown keys are rejected unless target constructor has `**kwargs`.
- `_type_` must resolve to an importable class.
- With base-class mode, `_type_` must be a subclass of configured class.
- Unsupported/complex constructor hints may be skipped during subfield build.
