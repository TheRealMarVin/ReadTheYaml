from readtheyaml.ui.widgets import (
    INVALID_INPUT,
    BoolFieldWidget,
    EnumFieldWidget,
    FloatFieldWidget,
    IntFieldWidget,
    StringFieldWidget,
    normalize_bool,
    normalize_enum,
    normalize_float,
    normalize_int,
    normalize_str,
)


def test_normalize_str_keeps_value():
    result = normalize_str("abc")
    assert result.value == "abc"
    assert result.error is None
    required_empty = normalize_str("   ", required=True)
    optional_empty = normalize_str("   ", required=False)
    assert required_empty.error == "Value is required."
    assert optional_empty.value is None


def test_normalize_int_success_and_failure():
    ok = normalize_int("42")
    bad = normalize_int("x")
    empty = normalize_int("  ", required=True)
    optional_empty = normalize_int("  ", required=False)

    assert ok.value == 42
    assert ok.error is None
    assert bad.value is None
    assert bad.error == "Expected an integer."
    assert empty.error == "Value is required."
    assert optional_empty.error is None
    assert optional_empty.value is None


def test_normalize_float_success_and_failure():
    ok = normalize_float("3.5")
    bad = normalize_float("x")
    optional_empty = normalize_float(" ", required=False)

    assert ok.value == 3.5
    assert ok.error is None
    assert bad.value is None
    assert bad.error == "Expected a float."
    assert optional_empty.value is None
    assert optional_empty.error is None


def test_normalize_bool_returns_plain_bool():
    assert normalize_bool(True).value is True
    assert normalize_bool(False).value is False


def test_normalize_enum_success_and_failure():
    ok = normalize_enum("dev", ["dev", "prod"])
    bad = normalize_enum("qa", ["dev", "prod"])

    assert ok.value == "dev"
    assert ok.error is None
    assert bad.value is None
    assert bad.error == "Expected one of the allowed values."


def test_widget_static_convert_helpers():
    assert StringFieldWidget.convert("x").value == "x"
    assert StringFieldWidget.convert(" ", required=True).error == "Value is required."
    assert IntFieldWidget.convert("9").value == 9
    assert IntFieldWidget.convert("bad").error == "Expected an integer."
    assert IntFieldWidget.convert("", required=False).value is None
    assert FloatFieldWidget.convert("1.25").value == 1.25
    assert BoolFieldWidget.convert(True).value is True
    assert EnumFieldWidget.convert("prod", ["dev", "prod"]).value == "prod"
    assert INVALID_INPUT is not None
