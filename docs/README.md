# Documentation Index

This page is the documentation entrypoint for both maintainers and users.

## How ReadTheYaml works

`ReadTheYaml` validates plain Python data loaded from YAML-compatible sources against
Python type hints.

At a high level:

1. You define a schema as Python typed structures (for example, tuples, lists, unions,
   enums, primitives, and nested objects).
2. `Schema` builds field validators from those hints.
3. `DataInstance` applies the schema to concrete input data.
4. Validation either succeeds with normalized/accepted values or raises structured
   validation/format errors.

Internally, field handlers in `readtheyaml.fields.base` and
`readtheyaml.fields.composite` cover primitive and composed types, and utility helpers
support type introspection and dispatch.

## Docs pages

| Page | What it covers |
| --- | --- |
| [`docs/README.md`](./README.md) | This index: architecture overview, doc navigation, and test coverage map. |
| [`README.md`](../README.md) | Package-level introduction, installation, and user-facing usage examples. |
| [`examples/schema.yaml`](../examples/schema.yaml) | Baseline schema shape used in examples. |
| [`examples/valid_config.yaml`](../examples/valid_config.yaml) | A valid configuration example to compare against schema expectations. |
| [`examples/invalid_config.yaml`](../examples/invalid_config.yaml) | An intentionally invalid config illustrating failure cases. |
| [`examples/schema_ref.yaml`](../examples/schema_ref.yaml) | Alternate/reference schema example for extended scenarios. |

## Coverage map (docs ↔ unit tests)

The documentation is anchored to unit-tested behavior.

| Docs page | Primary behavior area | Unit tests that define behavior |
| --- | --- | --- |
| [`README.md`](../README.md) | Public schema usage and top-level validation flow | [`tests/test_schema.py`](../tests/test_schema.py), [`tests/test_data_instance.py`](../tests/test_data_instance.py) |
| [`docs/README.md`](./README.md) | Internal validator model and behavior guarantees | [`tests/test_schema.py`](../tests/test_schema.py), [`tests/test_data_instance.py`](../tests/test_data_instance.py), [`tests/utils/test_type_utils.py`](../tests/utils/test_type_utils.py) |
| [`examples/schema.yaml`](../examples/schema.yaml) | Schema constructs shown in examples | [`tests/test_schema.py`](../tests/test_schema.py), [`tests/fields/base/*.py`](../tests/fields/base/), [`tests/fields/composite/*.py`](../tests/fields/composite/) |
| [`examples/valid_config.yaml`](../examples/valid_config.yaml) | Positive path configuration examples | [`tests/test_data_instance.py`](../tests/test_data_instance.py), [`tests/fields/base/*.py`](../tests/fields/base/), [`tests/fields/composite/*.py`](../tests/fields/composite/) |
| [`examples/invalid_config.yaml`](../examples/invalid_config.yaml) | Negative path and error-shaping examples | [`tests/test_data_instance.py`](../tests/test_data_instance.py), [`tests/fields/base/*.py`](../tests/fields/base/), [`tests/fields/composite/*.py`](../tests/fields/composite/) |
| [`examples/schema_ref.yaml`](../examples/schema_ref.yaml) | Reference schema variants and type-resolution behavior | [`tests/test_schema.py`](../tests/test_schema.py), [`tests/utils/test_type_utils.py`](../tests/utils/test_type_utils.py) |

## Documentation policy

Docs in this project are written to reflect **unit-tested behavior first**, and then
illustrative examples.
