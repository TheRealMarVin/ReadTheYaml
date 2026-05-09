# Editor

The ReadTheYAML editor is a Tkinter desktop app for editing YAML configs against a schema with live validation.

## Start the editor

```bash
python main_editor.py --schema schema.yaml --config config.yaml --strict true
```

Arguments:

- `--schema` (required): schema YAML path.
- `--config` (optional): config YAML path. If omitted, the editor starts from an empty config.
- `--strict` (optional, default `true`): strict-mode validation (`true|false`).

If the schema/config cannot be loaded, startup fails with an error dialog and non-zero exit.

## What the editor does

- Loads schema and config.
- Builds a schema model used by the UI tree and dialogs.
- Keeps an in-memory draft config while editing.
- Runs debounced validation through the same schema engine used by non-UI validation.
- Shows both export preview and full-with-defaults preview.
- Blocks saving while invalid.

At startup, missing required fields/sections are tolerated so partially complete configs can still be edited.

## Main UI parts

Left panel:

- Toolbar: `Load config`, `Save`, `Save Full`.
- Schema tree:
  - rows are fields/sections discovered from schema introspection;
  - value column shows current draft value, or default marker when field is unset and has a default;
  - color tags:
    - red: missing required field,
    - green: valid provided value,
    - gray: inactive due to `when`.

Right panel:

- Validation badge: `PENDING`, `VALID`, `INVALID`.
- Global errors pane.
- Fix-hints pane.
- YAML preview tabs:
  - `Export YAML`: user-facing payload preview.
  - `Full YAML (with defaults)`: expanded payload when config is valid.

Footer status:

- active schema/config names,
- dirty marker (`*`),
- strict-mode state.

## Editing workflow

Double-click tree rows:

- section row: opens read-only section info (path, required/optional, description, `when` text);
- field row: opens field editor dialog tailored to field type.

Field dialog behavior:

- `none`: no input needed, value is `null`;
- `bool`: checkbox;
- `enum`: combobox constrained to schema values;
- `object[...]`: class-path selector, constructor-parameter table, and extra kwargs YAML mapping;
- other scalar/composite fields: text entry parsed and validated against field constraints.

Validation is done in two layers:

1. local dialog validation for immediate field feedback;
2. debounced full-schema validation for global status and save enablement.

## Save behavior

`Save` and `Save Full` are enabled only when config is valid.

- `Save` always writes export config (preview-aligned payload).
- `Save Full` writes full config with schema defaults.
- If no config file is loaded yet, both actions prompt for a target path first.

Save writes UTF-8 YAML with `\n` line endings.

## Conditional visibility (`when`)

The editor computes a visibility map from current draft data:

- inactive fields/sections are grayed out in the tree;
- inactive nodes are skipped by validation and removed from built output paths, matching schema runtime behavior.

## Notes and limits

- Root config must be a mapping/dictionary.
- Invalid existing configs can still be opened if the issue is only missing required fields/sections.
- Save is intentionally blocked on validation errors.
