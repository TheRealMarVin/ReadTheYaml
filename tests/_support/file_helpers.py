from pathlib import Path
from shutil import rmtree
from textwrap import dedent
from typing import Any, Mapping

import yaml


def reset_test_dir(path: Path) -> Path:
    if path.exists():
        rmtree(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_yaml_file(base_dir: Path, relative_path: str, content: Any) -> Path:
    target = base_dir / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(content, str):
        payload = dedent(content).strip() + "\n"
        target.write_text(payload, encoding="utf-8")
    else:
        with open(target, "w", encoding="utf-8") as handle:
            yaml.safe_dump(content, handle, sort_keys=False)

    return target


def write_yaml_files(base_dir: Path, files: Mapping[str, Any]) -> dict[str, Path]:
    return {name: write_yaml_file(base_dir, name, content) for name, content in files.items()}
