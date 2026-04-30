# Conditions (`when`)

`when` lets one schema express conditional fields/sections based on other config values.
This avoids duplicating near-identical schemas for feature toggles and mode-specific branches.

You can use `when`:
- on a field definition
- on a subsection definition

If a `when` condition evaluates to `false`, that field/section is inactive:
- skipped during validation
- omitted from `built`
- removed/omitted from `data_with_default`

If a `when` condition evaluates to `true`, that node is active and normal required/default/type validation applies.

In strict mode, inactive nodes are still skipped:
- payload under an inactive field/section is ignored
- strict unknown-key checks still apply to normal active schema keys at each section
- unrelated unknown top-level keys are still rejected
- conditions that read paths inside an inactive section see that path as missing

## Atomic Condition Shape

```yaml
when:
  field: feature.enabled
  op: eq
  value: true
```

Required keys:
- `field` (non-empty dot path string)
- `op` (operator)

`value` is:
- required for comparison operators (`eq`, `ne`, `gt`, `ge`, `lt`, `le`, `in`, `not_in`)
- forbidden for presence operators (`exists`, `not_exists`)

## Combinators

Combinator forms:

```yaml
when:
  all:
    - field: mode
      op: in
      value: [prod, stage]
    - not:
        field: dry_run
        op: eq
        value: true
```

Supported combinators:
- `all` (logical AND)
- `any` (logical OR)
- `not` (logical NOT)

Aliases:
- `and` -> `all`
- `or` -> `any`
- `not` -> `not`

Rule:
- A combinator key cannot be mixed with other keys in the same object.

## Operators

Canonical operators:
- `eq`
- `ne`
- `gt`
- `ge`
- `lt`
- `le`
- `exists`
- `not_exists`
- `in`
- `not_in`

Accepted aliases:
- `equal`, `equals`, `==` -> `eq`
- `not_equal`, `!=` -> `ne`
- `>` -> `gt`
- `gte`, `>=` -> `ge`
- `<` -> `lt`
- `lte`, `<=` -> `le`
- `present` -> `exists`
- `missing` -> `not_exists`
- `nin` -> `not_in`

For `in` and `not_in`, `value` must be a list/tuple/set.

## Evaluation Behavior

- Path lookup (`field: a.b.c`) only traverses dictionaries.
- If a path is missing:
  - `exists` returns `false`
  - `not_exists` returns `true`
  - all other operators return `false`
- Type-incompatible comparisons (like `gt` across incompatible types) evaluate to `false` instead of raising.
- If a section is inactive due to its own `when`, payload under that section is ignored for other conditions.

## Default-Value Interaction

Conditions are evaluated against a context that includes optional defaults already injected.

Example:
- if `feature_enabled` is optional with default `false`
- and another field has `when: { field: feature_enabled, op: eq, value: true }`
- then that field stays disabled unless config explicitly sets `feature_enabled: true`

Optional subsection behavior:
- If an optional subsection is missing and has no explicit section `default`, it is omitted (not materialized).
- If an optional subsection has an explicit section `default`, that value is used.
- Nested field defaults inside an omitted optional subsection are not injected unless the subsection is active/present or has an explicit section default.

## Practical Example

```yaml
mode:
  type: str
  required: false
  default: dev

force:
  type: bool
  required: false
  default: false

deploy:
  type: str
  description: deploy target
  when:
    all:
      - any:
          - field: mode
            op: in
            value: [prod, stage]
          - field: force
            op: eq
            value: true
      - not:
          field: mode
          op: eq
          value: dry-run
```

## Practical `compile_enabled` Example

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
    required: true
```

Semantics for this example:
- if `compile_enabled` is `false`, `compile` is inactive (not validated, not in output)
- if `compile_enabled` is `true`, `compile` is active and `compile.command` is required

## Limitations / Non-goals

- `when` evaluates declarative condition objects only; it does not execute Python.
- Runtime object inspection is not available in this phase (for example checking object attributes/method results).
- Arbitrary Python expressions in YAML are not supported.
