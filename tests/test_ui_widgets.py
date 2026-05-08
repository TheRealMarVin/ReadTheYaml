from readtheyaml.ui.widgets import (
    INVALID_INPUT,
    BoolFieldWidget,
    EnumFieldWidget,
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
    assert BoolFieldWidget.convert(True).value is True
    assert EnumFieldWidget.convert("prod", ["dev", "prod"]).value == "prod"
    assert INVALID_INPUT is not None
