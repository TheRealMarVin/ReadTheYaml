import argparse
import sys
from pathlib import Path

from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.schema import Schema


def main():
    parser = argparse.ArgumentParser(
        description="Validate a YAML configuration file against a ReadTheYaml schema."
    )
    parser.add_argument("--schema", required=True, help="Path to the YAML schema definition file")
    parser.add_argument("--config", required=True, help="Path to the YAML configuration file to validate")

    args = parser.parse_args()

    try:
        schema = Schema.from_yaml(args.schema, Path("./examples"))
        validated_config = schema.validate_file(args.config, strict=False)
        print("✅ Config is valid!")
    except ValidationError as e:
        print(f"❌ Validation failed: {e}", file=sys.stderr)
        sys.exit(1)

    print(validated_config)


if __name__ == "__main__":
    main()
