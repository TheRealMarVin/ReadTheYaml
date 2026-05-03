from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Any
import re
from urllib.parse import urlparse

import yaml

from readtheyaml.conditions import parse_when
from readtheyaml.fields.field_factory import FIELD_FACTORY
from readtheyaml.fields.field_helpers import normalize_for_doc_dump
from readtheyaml.schema import Schema


@dataclass
class DocRow:
    path: str
    type_name: str
    description: str
    required: str
    default: str
    conditions: str


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return slug or "section"


def _source_label(source_id: str, docs_root: Path) -> str:
    if source_id.startswith("https://") or source_id.startswith("http://"):
        parsed = urlparse(source_id)
        name = Path(parsed.path).name or parsed.netloc
        return f"url:{name}"

    source_path = Path(source_id)
    try:
        return source_path.resolve().relative_to(docs_root.resolve()).as_posix()
    except ValueError:
        return source_path.name


def _load_yaml(source: str) -> Any:
    if source.startswith("https://") or source.startswith("http://"):
        import requests

        response = requests.get(source, timeout=10)
        response.raise_for_status()
        return yaml.safe_load(response.text)

    with open(source, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def _resolve_ref(ref: str, base_dir: Path) -> tuple[dict[str, Any], str, Path]:
    resolved, ref_base_dir = Schema._resolve_ref_and_base(ref, base_dir)
    if not isinstance(resolved, dict):
        raise ValueError(f"Referenced schema must be a mapping/dictionary, got {type(resolved).__name__}")

    if ref.startswith("https://") or ref.startswith("http://"):
        source_id = ref
    else:
        source_id = str((base_dir / ref).resolve())

    return resolved, source_id, ref_base_dir


def _format_when(value: Any) -> str:
    if value is None:
        return ""
    parsed = parse_when(value, "when")
    normalized = normalize_for_doc_dump(parsed)
    return yaml.safe_dump(normalized, sort_keys=False, default_flow_style=True).strip()


def _field_doc_constraints(name: str, node: dict[str, Any]) -> list[str]:
    type_name = node.get("type")
    if not isinstance(type_name, str):
        return []

    reserved = {"name", "type", "description", "required", "default", "when", "$ref"}
    extras = {k: v for k, v in node.items() if k not in reserved}
    try:
        field = FIELD_FACTORY.create_field(
            type_name,
            name,
            description=str(node.get("description", "")),
            required=node.get("required", True),
            default=node.get("default"),
            when=node.get("when"),
            **extras,
        )
    except Exception:
        return []

    return field.doc_constraints()


def _format_conditions(node: dict[str, Any], *, is_field: bool) -> str:
    parts: list[str] = []

    if "when" in node:
        when_repr = _format_when(node.get("when"))
        if when_repr:
            parts.append(f"Applies when: {when_repr}")

    if is_field:
        parts.extend(_field_doc_constraints(str(node.get("name", "")), node))

    return "\n".join(parts)


def _format_required(node: dict[str, Any]) -> str:
    return str(node.get("required", True))


def _format_default(node: dict[str, Any]) -> str:
    if "default" not in node:
        return ""
    return repr(node["default"])


def _walk_schema(
    schema_dict: dict[str, Any],
    *,
    section_path: str,
    base_dir: Path,
    ref_target_map: dict[str, str],
    rows: list[DocRow],
    dependencies: list[tuple[str, dict[str, Any], Path]],
    seen_dependencies: set[str],
) -> None:
    raw_when = schema_dict.get("when")
    has_section_when = "when" in schema_dict and not (
        isinstance(raw_when, dict) and ("type" in raw_when or "$ref" in raw_when)
    )

    for key, value in schema_dict.items():
        if key == "when" and has_section_when:
            continue
        if not isinstance(value, dict):
            continue

        path = f"{section_path}.{key}" if section_path else key
        description = str(value.get("description", ""))

        if "type" in value:
            value_with_name = {**value, "name": key}
            rows.append(
                DocRow(
                    path=path,
                    type_name=str(value["type"]),
                    description=description,
                    required=_format_required(value),
                    default=_format_default(value),
                    conditions=_format_conditions(value_with_name, is_field=True),
                )
            )
            continue

        if "$ref" in value:
            ref_value = str(value["$ref"])
            ref_dict, source_id, ref_base_dir = _resolve_ref(ref_value, base_dir)
            ref_alias = key
            if source_id not in ref_target_map:
                ref_target_map[source_id] = ref_alias
            target_label = ref_target_map.get(source_id, ref_alias)
            target_anchor = _slugify(f"schema-{target_label}")
            rows.append(
                DocRow(
                    path=path,
                    type_name=f'section (<a href="#{escape(target_anchor)}">{escape(ref_alias)}</a>)',
                    description=description,
                    required=_format_required(value),
                    default=_format_default(value),
                    conditions=_format_conditions(value, is_field=False),
                )
            )
            if source_id not in seen_dependencies:
                seen_dependencies.add(source_id)
                dependencies.append((source_id, ref_dict, ref_base_dir))
            continue

        rows.append(
            DocRow(
                path=path,
                type_name="section",
                description=description,
                required=_format_required(value),
                default=_format_default(value),
                conditions=_format_conditions(value, is_field=False),
            )
        )
        _walk_schema(
            value,
            section_path=path,
            base_dir=base_dir,
            ref_target_map=ref_target_map,
            rows=rows,
            dependencies=dependencies,
            seen_dependencies=seen_dependencies,
        )


def _build_table(title: str, anchor: str, rows: list[DocRow]) -> str:
    escaped_title = escape(title)
    sorted_rows = sorted(rows, key=lambda row: (row.required != "True", row.path))
    parts = [
        f'<h2 id="{escape(anchor)}">{escaped_title}</h2>',
        "<table>",
        "<thead><tr><th>Field Path</th><th>Type</th><th>Required</th><th>Description</th><th>Default</th><th>Conditions</th></tr></thead>",
        "<tbody>",
    ]
    for row in sorted_rows:
        parts.append(
            "<tr>"
            f"<td><code>{escape(row.path)}</code></td>"
            f"<td>{row.type_name}</td>"
            f"<td>{escape(row.required)}</td>"
            f"<td>{escape(row.description)}</td>"
            f"<td>{escape(row.default)}</td>"
            f'<td style="white-space: pre-line;">{escape(row.conditions)}</td>'
            "</tr>"
        )
    parts.append("</tbody></table>")
    return "\n".join(parts)


def build_schema_documentation_html(schema_file: str) -> str:
    schema_path = Path(schema_file).resolve()
    root_dict = _load_yaml(str(schema_path))
    if not isinstance(root_dict, dict):
        raise ValueError(f"Schema definition must be a mapping/dictionary, got {type(root_dict).__name__}")

    docs_root = schema_path.parent
    queue: list[tuple[str, dict[str, Any], Path]] = [(str(schema_path), root_dict, docs_root)]
    seen = {str(schema_path)}
    labels = {str(schema_path): _source_label(str(schema_path), docs_root)}
    sections_html: list[str] = []

    while queue:
        source_id, schema_dict, base_dir = queue.pop(0)
        rows: list[DocRow] = []
        discovered: list[tuple[str, dict[str, Any], Path]] = []

        _walk_schema(
            schema_dict,
            section_path="",
            base_dir=base_dir,
            ref_target_map=labels,
            rows=rows,
            dependencies=discovered,
            seen_dependencies=seen,
        )

        for dep_source_id, _, _ in discovered:
            if dep_source_id not in labels:
                labels[dep_source_id] = _source_label(dep_source_id, docs_root)

        label = labels.get(source_id, _source_label(source_id, docs_root))
        title = f"Schema: {label}"
        anchor = _slugify(f"schema-{label}")
        sections_html.append(_build_table(title, anchor, rows))
        queue.extend(discovered)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Schema Documentation</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; line-height: 1.4; }}
    h1 {{ margin-top: 0; }}
    h2 {{ margin-top: 28px; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 8px; }}
    th, td {{ border: 1px solid #d0d7de; padding: 8px; text-align: left; vertical-align: top; }}
    th {{ background: #f6f8fa; }}
    code {{ background: #f6f8fa; padding: 1px 4px; border-radius: 4px; }}
  </style>
</head>
<body>
  <h1>Schema Documentation</h1>
  {"".join(sections_html)}
</body>
</html>
"""


def write_schema_documentation_html(schema_file: str, output_file: str) -> None:
    html = build_schema_documentation_html(schema_file)
    output_path = Path(output_file)
    output_path.write_text(html, encoding="utf-8")
