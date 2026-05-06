from readtheyaml.ui.widgets import (
    INVALID_INPUT,
    BoolFieldWidget,
    EnumFieldWidget,
    FloatFieldWidget,
    IntFieldWidget,
    StringFieldWidget,
)


def test_widget_string_convert_keeps_value():
    result = StringFieldWidget.convert("abc")
    assert result.value == "abc"
    assert result.error is None
    required_empty = StringFieldWidget.convert("   ", required=True)
    optional_empty = StringFieldWidget.convert("   ", required=False)
    assert required_empty.error == "Value is required."
    assert optional_empty.value is None


def test_widget_int_convert_success_and_failure():
    ok = IntFieldWidget.convert("42")
    bad = IntFieldWidget.convert("x")
    empty = IntFieldWidget.convert("  ", required=True)
    optional_empty = IntFieldWidget.convert("  ", required=False)

    assert ok.value == 42
    assert ok.error is None
    assert bad.value is None
    assert bad.error is not None
    assert "int" in bad.error.lower()
    assert empty.error == "Value is required."
    assert optional_empty.error is None
    assert optional_empty.value is None


def test_widget_float_convert_success_and_failure():
    ok = FloatFieldWidget.convert("3.5")
    bad = FloatFieldWidget.convert("x")
    optional_empty = FloatFieldWidget.convert(" ", required=False)

    assert ok.value == 3.5
    assert ok.error is None
    assert bad.value is None
    assert bad.error is not None
    assert "float" in bad.error.lower()
    assert optional_empty.value is None
    assert optional_empty.error is None


def test_widget_bool_convert_returns_plain_bool():
    assert BoolFieldWidget.convert(True).value is True
    assert BoolFieldWidget.convert(False).value is False


def test_widget_enum_convert_success_and_failure():
    ok = EnumFieldWidget.convert("dev", ["dev", "prod"])
    bad = EnumFieldWidget.convert("qa", ["dev", "prod"])

    assert ok.value == "dev"
    assert ok.error is None
    assert bad.value is None
    assert bad.error is not None


def test_widget_static_convert_helpers():
    assert StringFieldWidget.convert("x").value == "x"
    assert StringFieldWidget.convert(" ", required=True).error == "Value is required."
    assert IntFieldWidget.convert("9").value == 9
    assert IntFieldWidget.convert("bad").error is not None
    assert IntFieldWidget.convert("", required=False).value is None
    assert FloatFieldWidget.convert("1.25").value == 1.25
    assert BoolFieldWidget.convert(True).value is True
    assert EnumFieldWidget.convert("prod", ["dev", "prod"]).value == "prod"
    assert INVALID_INPUT is not None
