# ReadTheYAML

ReadTheYAML validates YAML config files against a schema, injects defaults, and returns a validated config object.

## Installation

```bash
pip install ReadTheYAML
```

Local development install:

```bash
git clone https://github.com/TheRealMarVin/ReadTheYAML.git
cd ReadTheYAML
pip install -e .
```

## What it supports

- Required and optional fields
- Default values for optional fields
- Primitive and composite types
- Nested sections
- Strict mode (reject unknown keys) and non-strict mode (pass through unknown keys)
- Schema composition with `$ref` (local files and HTTP URLs)

## Quick start

Schema (`schema.yaml`):

```yaml
service_name:
  type: str
  description: service display name

port:
  type: int
  description: service port
  required: false
  default: 8080
  min_value: 1
  max_value: 65535

logging:
  $ref: ./shared/logging.yaml
  required: false
```

Config (`config.yaml`):

```yaml
service_name: api-gateway
```

Python usage:

```python
from readtheyaml.schema import Schema

schema = Schema.from_yaml("schema.yaml")
built, data_with_default = schema.validate_file("config.yaml", strict=True)

print(built)              # validated/built config
print(data_with_default)  # config with injected defaults
```

## CLI usage

This repository currently exposes a CLI through `main.py`:

```bash
python main.py --schema schema.yaml --config config.yaml
```

## Type syntax overview

Primitive types:

- `any`
- `None`
- `bool`
- `int`
- `float`
- `str`
- `enum` (requires `values`)

Composite types:

- `list[T]`
- `tuple[T1, T2, ...]`
- `union[A, B]` or `A | B`
- `object[package.module.ClassName]` (or `object` with `_type_` in data)

Common field options:

- `description`
- `required`
- `default`
- `min_value` / `max_value` / `value_range`
- `min_length` / `max_length` / `length_range`

## Notes

- Field names cannot use reserved constructor keywords.
- Optional fields usually require a valid `default`.
- HTTP `$ref` resolution imports `requests` at runtime.

## Documentation

See [docs/index.md](docs/index.md) for a full type reference and behavior notes.

## Running tests

```bash
pytest
```

## Status

[![Run Unit Tests](https://github.com/TheRealMarVin/ReadTheYAML/actions/workflows/test.yml/badge.svg)](https://github.com/TheRealMarVin/ReadTheYAML/actions/workflows/test.yml)
