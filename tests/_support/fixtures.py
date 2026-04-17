from pathlib import Path
from os import getenv
from re import sub
from shutil import rmtree

import pytest

from tests._support.file_helpers import reset_test_dir, write_yaml_files


def _should_keep_test_files(request) -> bool:
    if request.config.getoption("--keep-test-files"):
        return True

    value = getenv("READTHEYAML_KEEP_TEST_FILES", "").strip().lower()
    return value in {"1", "true", "yes", "on"}


@pytest.fixture
def schema_examples_dir(request) -> Path:
    tests_dir = Path(__file__).resolve().parents[1]
    run_root = tests_dir / ".tmp" / "schema_examples"

    safe_name = sub(r"[^A-Za-z0-9_.-]+", "_", request.node.nodeid)
    test_dir = run_root / safe_name
    reset_test_dir(test_dir)

    yield test_dir

    if not _should_keep_test_files(request) and test_dir.exists():
        rmtree(test_dir)


@pytest.fixture
def create_schema_examples(schema_examples_dir: Path):
    def _create(files: dict[str, object]) -> dict[str, Path]:
        return write_yaml_files(schema_examples_dir, files)

    return _create
