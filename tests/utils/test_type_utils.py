from readtheyaml.utils.type_utils import type_to_string, get_params_and_defaults


def test_type_to_string_builtin():
    """Test string output for builtin types like int and str."""
    assert type_to_string(int) == "int"
    assert type_to_string(str) == "str"


def test_type_to_string_union():
    """Test string output for Union types."""
    assert type_to_string(int | None) == "int | None"
    assert type_to_string(str | int) == "str | int"


def test_type_to_string_generic():
    """Test string output for generic types like list[int] or dict[str, int]."""
    assert type_to_string(list[int]) == "list[int]"
    assert type_to_string(dict[str, int]) == "dict[str, int]"


def test_type_to_string_nested():
    """Test nested generic type output."""
    nested = dict[str, list[int | None]]
    assert type_to_string(nested) == "dict[str, list[int | None]]"


def test_type_to_string_custom_class():
    """Test custom class formatting includes module path."""
    class MyCustomClass:
        pass

    expected = f"object[{MyCustomClass.__module__}.MyCustomClass]"
    assert type_to_string(MyCustomClass) == expected


# --- get_params_and_defaults tests ---

def test_get_params_and_defaults_basic():
    """Test parameter introspection for class with no defaults."""
    class MyClass:
        def __init__(self, a: int, b: str):
            pass

    out = get_params_and_defaults(MyClass)
    assert out["a"]["has_hint"] is True
    assert out["a"]["hint"] == int
    assert out["a"]["has_default"] is False
    assert out["a"]["default"] is None

    assert out["b"]["hint"] == str


def test_get_params_and_defaults_with_defaults():
    """Test default value detection and hint presence."""
    class MyClass:
        def __init__(self, a: int = 5, b: str = "hi"):
            pass

    out = get_params_and_defaults(MyClass)
    assert out["a"]["has_default"] is True
    assert out["a"]["default"] == 5
    assert out["b"]["default"] == "hi"


def test_get_params_and_defaults_no_hints():
    """Test behavior when type hints are not present."""
    class MyClass:
        def __init__(self, x, y=42):
            pass

    out = get_params_and_defaults(MyClass)
    assert out["x"]["has_hint"] is False
    assert out["x"]["hint"] is None
    assert out["y"]["has_default"] is True
    assert out["y"]["default"] == 42


def test_get_params_and_defaults_union():
    """Test type hint with union types like int | None."""
    class MyClass:
        def __init__(self, maybe: int | None):
            pass

    out = get_params_and_defaults(MyClass)
    assert out["maybe"]["hint"] == (int | None)


def test_get_params_and_defaults_complex():
    """Test mix of hints, defaults, and no hints."""
    class MyClass:
        def __init__(self, a, b: str = "x", c: list[int] = [1, 2]):
            pass

    out = get_params_and_defaults(MyClass)
    assert out["a"]["has_hint"] is False
    assert out["b"]["hint"] == str
    assert out["b"]["default"] == "x"
    assert out["c"]["hint"] == list[int]
    assert out["c"]["default"] == [1, 2]
