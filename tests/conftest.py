from tests._support.fixtures import create_schema_examples, schema_examples_dir

__all__ = ["schema_examples_dir", "create_schema_examples"]


def pytest_addoption(parser):
    parser.addoption(
        "--keep-test-files",
        action="store_true",
        default=False,
        help="Keep generated files under tests/.tmp after test execution.",
    )
