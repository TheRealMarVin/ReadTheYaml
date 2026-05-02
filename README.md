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
- Conditional fields/sections with `when`
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

# Generate HTML documentation from a schema
python main.py --schema schema.yaml --generate-doc --output schema-doc.html
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

## Conditions (`when`)

`when` exists so one schema can express conditional fields/sections without splitting into multiple schemas.
It gates validation and output inclusion based on other config values known at schema-validation time.

Practical example (`compile_enabled` toggles a `compile` section):

```yaml
compile_enabled:
  type: bool
  required: false
  default: false

compile:
  required: false
  when:
    field: compile_enabled
    op: eq
    value: true
  command:
    type: str
    description: Compile command
    required: true
```

If `compile_enabled` is `false`, `compile` is skipped.
If `compile_enabled` is `true`, `compile.command` is validated and required.

Syntax reference:
- Atomic condition:
  - `when: { field: some.path, op: eq, value: 123 }`
- Logical combinators:
  - `all: [...]` (AND)
  - `any: [...]` (OR)
  - `not: {...}` (NOT)

Semantics:
- Active node (`when` is true):
  - validated normally
  - included in `built`
  - included in `data_with_default` (with defaults applied as needed)
- Inactive node (`when` is false):
  - not validated
  - omitted from `built`
  - removed/omitted from `data_with_default`
- If an optional subsection is missing and has no explicit section `default`, it is omitted (not auto-materialized from child defaults).
- If a subsection is inactive due to `when`, payload under that subsection is ignored when evaluating other `when` conditions.

Limitations / non-goals for this phase:
- `when` does not inspect runtime Python objects or object internals.
- `when` does not evaluate arbitrary Python expressions from YAML.

Full reference (operators, aliases, combinators): [docs/conditions.md](docs/conditions.md)

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
