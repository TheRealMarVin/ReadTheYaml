# ReadTheYaml

> A lightweight YAML schema validator with just enough structure to stop future-you from asking: "Why the heck did I set this to 42?"

## What is this?

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

## What can it do?

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
## Supported Schema Types

ReadTheYAML provides a flexible and expressive way to define and validate data structures using YAML. Below is an overview of the supported types, their syntax, and usage examples. I tried to follow the standard of type hints in Python, but I relaxed some constraints.

### 🔹 Basic Types

* `None`: Represents None.
* `int`: Represents integer values.
* `float`: Represents floating-point numbers.
* `str`: Represents string values.
* `bool`: Represents boolean values (`true` or `false`).

**Example:**

```yaml
type: int
```

### 🔹 Composite Types

#### List

Defines a list of elements of a specified type.

**Syntax:**

```yaml
type: list[<element_type>]
```

**Example:**

```yaml
type: list[int]
```

#### Tuple

Defines a fixed-size sequence of elements, each with a specified type.

**Syntax:**

```yaml
type: tuple[<type1>, <type2>, ...]
```

**Example:**

```yaml
type: tuple[int, str]
```

#### Union

Specifies that a value can be of one of several types.

**Syntax:**

```yaml
type: union[<type1>, <type2>, ...]
```

**Example:**

```yaml
type: union[int, str]
```

### 🔹 Optional Types

To indicate that a field is optional (i.e., it can be `null`), include `None` in a `union`.

**Example:**

```yaml
type: union[int, None]
```

Alternatively, you can use the shorthand:

```yaml
type: int | None
```

### 🔹 Syntax Variations

ReadTheYAML supports both square brackets `[]` and parentheses `()` for defining composite types. However, the opening and closing brackets must match.

**Valid:**

```yaml
type: tuple[int, str]
type: tuple(int, str)
```

**Invalid:**

```yaml
type: tuple[int, str)
type: tuple(int, str]
```

### 🔹 Nested Types

You can nest composite types to define complex structures.

**Example:**

```yaml
type: list[tuple[int, str]]
```

This defines a list where each element is a tuple containing an integer and a string.

### 🔹 Field Options

Fields can have additional options to control validation and behavior:

* `description`: Provides a human-readable description of the field. This one is mandatory
* `required`: Indicates whether the field is mandatory. By default, the value is false (the field is not required).
* `default`: Specifies a default value if the field is omitted. This is mandatory when required is set to false.


**Example:**

```yaml
name:
  type: str
  required: true
  default: Unnamed
  description: The name of the entity.
```

---

## Example schema.yaml

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

## How to Use

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
## Contributions
If you try this out and find something confusing or missing — feel free to open an issue or suggestion. This project is a work-in-progress, but built with love and frustration.
