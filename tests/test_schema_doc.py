from pathlib import Path

from readtheyaml.schema_doc import build_schema_documentation_html


def test_build_schema_documentation_html_includes_refs_fields_and_conditions(tmp_path: Path):
    shared_dir = tmp_path / "shared"
    shared_dir.mkdir()

    (shared_dir / "logging.yaml").write_text(
        """
level:
  type: enum
  description: logging level
  values: [debug, info, warning]
""".strip(),
        encoding="utf-8",
    )

    schema_path = tmp_path / "schema.yaml"
    schema_path.write_text(
        """
service:
  type: str
  description: service name
  required: true
  min_length: 3

compile:
  required: false
  when:
    field: service
    op: eq
    value: api
  command:
    type: str
    description: compile command

logging:
  $ref: ./shared/logging.yaml
  required: false
  description: logging section
""".strip(),
        encoding="utf-8",
    )

    html = build_schema_documentation_html(str(schema_path))

    assert "service" in html
    assert "service name" in html
    assert "min_length" in html
    assert "when=" in html
    assert '<a href="#schema-logging">logging</a>' in html
    assert "Schema: schema.yaml" in html
    assert "Schema: logging" in html
    assert 'id="schema-logging"' in html
    assert "logging level" in html
