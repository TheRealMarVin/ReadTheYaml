import argparse
import sys
from pathlib import Path

import yaml

from readtheyaml.data_instance import DataInstance
from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.schema import Schema
from readtheyaml.schema_doc import write_schema_documentation_html


def main():
    parser = argparse.ArgumentParser(
        description="Validate YAML configs or generate HTML documentation from a ReadTheYAML schema."
    )
    parser.add_argument("--schema", required=True, help="Path to the YAML schema definition file")
    parser.add_argument("--config", help="Path to the YAML configuration file to validate")
    parser.add_argument(
        "--generate-doc",
        action="store_true",
        help="Generate HTML documentation from the schema instead of validating a config.",
    )
    parser.add_argument(
        "--output",
        default="schema-doc.html",
        help="Output HTML file path for --generate-doc (default: schema-doc.html).",
    )

    args = parser.parse_args()

    if args.generate_doc:
        write_schema_documentation_html(args.schema, args.output)
        print(f"Documentation generated: {args.output}")
        return

    if not args.config:
        parser.error("--config is required unless --generate-doc is used.")

    try:
        yaml_path = Path(args.config)
        with open(yaml_path, "r", encoding="utf-8") as f:
            yaml_data = yaml.safe_load(f)

        schema = Schema.from_yaml(args.schema, Path("./examples"))
        data_instance = DataInstance(data=yaml_data, schema=schema, strict=False)
        print("✅ Config is valid!")
    except ValidationError as e:
        print(f"❌ Validation failed: {e}", file=sys.stderr)
        sys.exit(1)

    print(data_instance.dump(file=None))


if __name__ == "__main__":
    main()
