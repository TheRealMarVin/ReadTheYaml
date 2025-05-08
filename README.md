# ReadTheYaml

> A lightweight YAML schema validator with just enough structure to stop future-you from asking: "Why the heck did I set this to 42?"

## 🧭 What is this?

**ReadTheYaml** is a Python library that helps you define, validate, and document your YAML configuration files. It was built by someone who got tired of forgetting:

- Which config values were required vs optional
- Why a given field was there in the first place
- What values are valid

It enforces structure in your YAML and documents everything along the way.

There might be more mature alternatives out there (really!), but this one's small, readable, and purpose-built for when you're tired of guessing your own project settings.


---

## 📦 Installation

```bash
pip install ReadTheYaml
```

Alternatively, clone the repo and install locally:

```bash
git clone https://github.com/TheRealMarVin/ReadTheYaml.git
cd ReadTheYaml
pip install -e .
```

---

## ✅ What can it do?

### 🔹 Validate YAML config files
It ensures all required fields are present, types are correct, and defaults are filled in where needed.

### 🔹 Support optional and required fields with descriptions
So future-you (or teammates) know what a setting is for.

### 🔹 Provide default values
Optional fields can define a default that will be added if missing.

### 🔹 Define valid numeric ranges
So you don’t accidentally open port `99999`.

### 🔹 Support nested schemas
Schemas can have sections inside sections (deeply nested).

### 🔹 Modular design with `$ref`
Subsections can live in their own YAML files and be reused across multiple schemas.

---

## 📄 Examples

### 🔹 `schema.yaml` (no `$ref`)
```yaml
name: app_config
subsections:
  network:
    required: true
    subsections:
      server:
        required: true
        fields:
          host:
            type: str
            required: true
            description: Host address to bind to
          port:
            type: int
            default: 8080
            range: [1, 65535]
```

### 🔹 `schema_ref.yaml` (with `$ref`)
```yaml
name: app_config
subsections:
  network:
    required: true
    subsections:
      server:
        $ref: ./shared/server.yaml
        required: true

  logging:
    $ref: ./shared/logging.yaml
    required: false
```

### 🔹 `server.yaml`
```yaml
description: HTTP server settings
fields:
  host:
    type: str
    required: true
    description: Host address to bind to
  port:
    type: int
    required: false
    default: 8080
    range: [1, 65535]
```

### 🔹 `valid_config.yaml`
```yaml
network:
  server:
    host: "127.0.0.1"
```

Even though `port` wasn’t specified, it will be filled in as `8080` because it's optional and has a default.

If `logging` was not included at all in the config, that’s fine — because it's marked `required: false`.


---

## 🛠️ How to Use

### 1. Validate a file with CLI
```bash
python -m ReadTheYaml.cli --schema schema.yaml --config valid_config.yaml
```

You’ll see:
```
✅ Config is valid!
```

Or, if you mess something up:
```
❌ Validation failed: [network.server.port] must be between 1 and 65535
```

### 2. Programmatic usage
```python
from ReadTheYaml.schema import Schema

try:
    schema = Schema.from_yaml("schema.yaml")
    validated_config = schema.validate_file("valid_config.yaml")
    print(validated_config)
except Exception as e:
    print(f"⚠️ Failed to load or validate config: {e}")
```

This returns a `dict` that includes:
- All your original values
- Any **default values** added automatically

---

## 🔍 Design Philosophy
- Every field has a purpose — documented inline
- Optional vs required is explicit
- Configs should validate **before** you use them
- Modular design: break down schema into reusable parts

---

## 📬 Contributions
If you try this out and find something confusing or missing — feel free to open an issue or suggestion. This project is a work-in-progress, but built with love and frustration.
