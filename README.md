# ReadTheYaml

> A lightweight YAML schema validator with just enough structure to stop future-you from asking: "Why the heck did I set this to 42?"

## 🧭 What is this?

**ReadTheYaml** is a Python library that helps you define, validate, and document your YAML configuration files. It was built by someone (me) who got tired of forgetting:

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

### 🔹 Define valid numeric or length ranges
So you don’t accidentally open port `99999` or supply an empty list.

### 🔹 Support list validation
You can define `list(int)`, `list(str)`, or even `list(nested(...))` to validate list content with precision.

### 🔹 Define enum fields
You can restrict values to a fixed set of strings using `EnumField` or `type: enum`.

### 🔹 Modular design with `$ref`
Schemas can include and reuse other schemas stored in separate files.

---

## 📄 Example schema.yaml

```yaml
name: app_config

status:
  type: enum
  enum: [pending, approved, rejected]
  required: true

retries:
  type: int
  default: 3
  min_value: 0
  max_value: 10

servers:
  type: list(nested(Server))
  length_range: [1, 5]

tags:
  type: list(str)
  min_length: 1

Server:
  host:
    type: str
    required: true
  port:
    type: int
    default: 8080
    min_value: 1
    max_value: 65535
```

---

## 🛠️ How to Use

### 1. Validate a file with CLI
```bash
python -m ReadTheYaml.cli --schema schema.yaml --config config.yaml
```

You’ll see:
```
✅ Config is valid!
```

Or, if something’s off:
```
❌ Validation failed: [status] must be one of: pending, approved, rejected
```

### 2. Programmatic usage
```python
from readtheyaml.schema import Schema

try:
    schema = Schema.from_yaml("schema.yaml")
    validated_config = schema.validate_file("config.yaml")
    print(validated_config)
except Exception as e:
    print(f"⚠️ Failed to load or validate config: {e}")
```
---
## 📬 Contributions
If you try this out and find something confusing or missing — feel free to open an issue or suggestion. This project is a work-in-progress, but built with love and frustration.
