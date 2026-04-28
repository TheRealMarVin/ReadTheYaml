# Conditions (`when`)

`when` lets you enable/disable a field or subsection based on other values in the config.

You can use `when`:
- on a field definition
- on a subsection definition

If a `when` condition evaluates to `false`, that field/section is skipped during validation and omitted from built output.

In strict mode, inactive nodes are still skipped:
- payload under an inactive field/section is ignored
- strict unknown-key checks still apply to normal active schema keys at each section
- unrelated unknown top-level keys are still rejected

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

## Default-Value Interaction

Conditions are evaluated against a context that includes optional defaults already injected.

Example:
- if `feature_enabled` is optional with default `false`
- and another field has `when: { field: feature_enabled, op: eq, value: true }`
- then that field stays disabled unless config explicitly sets `feature_enabled: true`

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
