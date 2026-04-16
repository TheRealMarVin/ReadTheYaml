import pytest

from readtheyaml.exceptions.format_error import FormatError
from readtheyaml.exceptions.validation_error import ValidationError
from readtheyaml.fields.base.string_field import StringField


# def test_validate_string_converts_empty_string():
#     """Test that StringField converts empty string correctly."""
#     field = StringField(name="new_field", description="My description", required=False, default="",
#                        min_length=0, max_length=-1, cast_to_string=True)
#     assert field.validate_and_build("") == ""
#
# def test_validate_string_converts_none_string():
#     """Test that StringField converts 'None' string correctly."""
#     field = StringField(name="new_field", description="My description", required=False, default="",
#                        min_length=0, max_length=-1, cast_to_string=True)
#     assert field.validate_and_build("None") == "None"
#
# def test_validate_string_converts_none_to_empty_string():
#     """Test that StringField converts None to empty string when not required."""
#     field = StringField(name="new_field", description="My description", required=False, default="",
#                        min_length=0, max_length=-1, cast_to_string=True)
#     assert field.validate_and_build(None) == "None"
#
# def test_validate_string_converts_number_string():
#     """Test that StringField converts number string correctly."""
#     field = StringField(name="new_field", description="My description", required=False, default="",
#                        min_length=0, max_length=-1, cast_to_string=True)
#     assert field.validate_and_build("123") == "123"
#
# def test_validate_string_converts_integer():
#     """Test that StringField converts integer to string."""
#     field = StringField(name="new_field", description="My description", required=False, default="",
#                        min_length=0, max_length=-1, cast_to_string=True)
#     assert field.validate_and_build(123) == "123"
#
# def test_validate_string_handles_none():
#     """Test that StringField handles None values when not required."""
#     field = StringField(name="new_field", description="My description", required=False, default="",
#                        min_length=0, max_length=-1, cast_to_string=True)
#     assert field.validate_and_build(None) == "None"
#
# def test_validate_string_rejects_none_when_required():
#     """Test that StringField rejects None when required is True."""
#     field = StringField(name="new_field", description="My description", required=True, default="",
#                        min_length=0, max_length=-1, cast_to_string=False)
#     with pytest.raises(ValidationError, match="Cannot be None"):
#         field.validate_and_build(None)
#
# def test_validate_string_without_casting():
#     """Test that StringField rejects non-string values when cast_to_string is False."""
#     field = StringField(name="new_field", description="My description", required=False, default="",
#                        min_length=0, max_length=-1, cast_to_string=False)
#     # String input should work
#     assert field.validate_and_build("test") == "test"
#     # Non-string input should raise error
#     with pytest.raises(ValidationError):
#         field.validate_and_build(123)
#
# def test_validate_string_rejects_invalid_default():
#     """Test that invalid default values raise FormatError."""
#     with pytest.raises(FormatError):
#         StringField(name="new_field", description="My description", required=False, default=None,
#                    min_length=0, max_length=-1, cast_to_string=False)
#
#
# def test_validate_string_rejects_none_string_when_disabled():
#     """Test that StringField rejects 'None' string when cast_to_string is False."""
#     field = StringField(name="new_field", description="My description", required=False, default="some_value",
#                       min_length=0, max_length=-1, cast_to_string=False)
#     with pytest.raises(ValidationError, match="Expected string"):
#         field.validate_and_build(None)
#
# def test_validate_string_rejects_none_when_disabled():
#     """Test that StringField rejects None when cast_to_string is False."""
#     field = StringField(name="new_field", description="My description", required=False, default="some_value",
#                       min_length=0, max_length=-1, cast_to_string=False)
#     with pytest.raises(ValidationError, match="Expected string"):
#         field.validate_and_build(None)
#
# def test_validate_string_rejects_negative_min_length():
#     """Test that StringField rejects negative min_length."""
#     with pytest.raises(FormatError, match="smaller than 0"):
#         StringField(name="new_field", description="My description", required=False, default="SomeString",
#                    min_length=-1, max_length=-1, cast_to_string=True)
#
# def test_validate_string_rejects_max_less_than_min():
#     """Test that StringField rejects max_length less than min_length."""
#     with pytest.raises(FormatError, match="smaller than min"):
#         StringField(name="new_field", description="My description", required=False, default="SomeString",
#                    min_length=10, max_length=0, cast_to_string=True)
#
# def test_validate_string_rejects_default_shorter_than_min():
#     """Test that StringField rejects default value shorter than min_length."""
#     with pytest.raises(FormatError, match="invalid default value"):
#         StringField(name="new_field", description="My description", required=False, default="SomeString",
#                    min_length=15, max_length=100, cast_to_string=True)
#
# def test_validate_string_rejects_value_shorter_than_min():
#     """Test that StringField rejects value shorter than min_length."""
#     field = StringField(name="new_field", description="My description", required=False,
#                        default="SomeLongLongString", min_length=15, max_length=100,
#                        cast_to_string=True)
#     with pytest.raises(ValidationError, match="Value must be at least"):
#         field.validate_and_build("SomeString")
#
# def test_validate_string_rejects_value_longer_than_max():
#     """Test that StringField rejects value longer than max_length."""
#     field = StringField(name="new_field", description="My description", required=False,
#                        default="test", min_length=0, max_length=5,
#                        cast_to_string=True)
#     with pytest.raises(ValidationError, match="Value must be at most"):
#         field.validate_and_build("SomeString")
#
# def test_validate_string_preserves_leading_trailing_whitespace():
#     """Test that leading and trailing whitespace is preserved in string values."""
#     field = StringField(name="new_field", description="Leading/trailing whitespace test",
#                        required=False, default="default", min_length=0, max_length=20,
#                        cast_to_string=False)
#     assert field.validate_and_build("  test  ") == "  test  "
#
#
# def test_validate_string_preserves_internal_whitespace():
#     """Test that internal whitespace is preserved in string values."""
#     field = StringField(name="new_field", description="Internal whitespace test",
#                        required=False, default="default", min_length=0, max_length=20,
#                        cast_to_string=False)
#     assert field.validate_and_build("test string") == "test string"
#
#
# def test_validate_string_handles_only_whitespace():
#     """Test that strings containing only whitespace are handled correctly."""
#     field = StringField(name="new_field", description="Whitespace-only test",
#                        required=False, default="default", min_length=0, max_length=20,
#                        cast_to_string=False)
#     assert field.validate_and_build("   ") == "   "
#
# def test_validate_string_unicode_characters():
#     """Test that Unicode characters are handled correctly."""
#     field = StringField(name="new_field", description="Handles Unicode", required=False,
#                        default="default", min_length=0, max_length=-1, cast_to_string=False)
#
#     # Test various Unicode characters
#     test_strings = [
#         "こんにちは",  # Japanese
#         "Привет",     # Russian
#         "مرحبا",      # Arabic
#         "😊👍🌟"       # Emojis
#     ]
#
#     for s in test_strings:
#         assert field.validate_and_build(s) == s
#
# def test_validate_string_empty_string():
#     """Test that an empty string is accepted when min_length is 0."""
#     field = StringField(name="new_field", description="Empty string test", required=False,
#                        default="", min_length=0, max_length=100, cast_to_string=True)
#     assert field.validate_and_build("") == ""
#
#
# def test_validate_string_long_string_rejected():
#     """Test that a string longer than max_length raises ValidationError."""
#     field = StringField(name="new_field", description="Long string test", required=False,
#                        default="", min_length=0, max_length=100, cast_to_string=True)
#     long_string = "x" * 1000
#     with pytest.raises(ValidationError, match="at most 100 characters"):
#         field.validate_and_build(long_string)
#
#
# def test_validate_string_control_characters():
#     """Test that strings with control characters are handled correctly."""
#     field = StringField(name="new_field", description="Control chars test", required=False,
#                        default="", min_length=0, max_length=100, cast_to_string=True)
#     assert field.validate_and_build("line1\nline2\r\nline3") == "line1\nline2\r\nline3"
#
# def test_validate_string_handles_none_strings():
#     """Test that string 'None' variations are handled as regular strings."""
#     field = StringField(name="new_field", description="None handling", required=False,
#                        default="default", min_length=0, max_length=100, cast_to_string=True)
#
#     # These should all be treated as regular strings
#     assert field.validate_and_build("None") == "None"
#     assert field.validate_and_build("none") == "none"
#     assert field.validate_and_build("NONE") == "NONE"
#
#
# def test_validate_string_without_casting_handles_strings():
#     """Test that string inputs work when cast_to_string is False."""
#     field = StringField(name="new_field", description="String handling", required=False,
#                        default="", min_length=0, max_length=100, cast_to_string=False)
#
#     # Regular strings should work fine
#     assert field.validate_and_build("test") == "test"
#     assert field.validate_and_build("None") == "None"  # Treated as regular string
#     assert field.validate_and_build("123") == "123"    # Numbers as strings are fine
#
#     # Non-string inputs should raise error
#     with pytest.raises(ValidationError, match="Expected string"):
#         field.validate_and_build(123)  # Integer
#     with pytest.raises(ValidationError, match="Expected string"):
#         field.validate_and_build(True)  # Boolean
#
#
# def test_validate_string_rejects_none_when_required():
#     """Test that None value is rejected when required is True."""
#     field = StringField(name="new_field", description="None handling", required=False,
#                        default="default", min_length=0, max_length=100, cast_to_string=False)
#
#     with pytest.raises(ValidationError):
#         field.validate_and_build(None)
#
# def test_validate_string_exact_min_length():
#     """Test that a string with exact min_length is accepted."""
#     field = StringField(name="new_field", description="Min length test", required=False,
#                        default="123", min_length=3, max_length=5, cast_to_string=True)
#     assert field.validate_and_build("123") == "123"
#
#
# def test_validate_string_exact_max_length():
#     """Test that a string with exact max_length is accepted."""
#     field = StringField(name="new_field", description="Max length test", required=False,
#                        default="123", min_length=3, max_length=5, cast_to_string=True)
#     assert field.validate_and_build("12345") == "12345"
#
#
# def test_validate_string_below_min_length():
#     """Test that a string below min_length raises ValidationError."""
#     field = StringField(name="new_field", description="Below min test", required=False,
#                        default="123", min_length=3, max_length=5, cast_to_string=True)
#     with pytest.raises(ValidationError, match="at least 3 characters"):
#         field.validate_and_build("12")
#
#
# def test_validate_string_above_max_length():
#     """Test that a string above max_length raises ValidationError."""
#     field = StringField(name="new_field", description="Above max test", required=False,
#                        default="123", min_length=3, max_length=5, cast_to_string=True)
#     with pytest.raises(ValidationError, match="at most 5 characters"):
#         field.validate_and_build("123456")
#
# def test_validate_string_special_characters():
#     """Test that special characters are handled correctly."""
#     field = StringField(name="new_field", description="Special chars", required=False,
#                        default="default", min_length=0, max_length=100, cast_to_string=True)
#
#     special_strings = [
#         "!@#$%^&*()_+-=[]{}|;':\",./<>?",  # Special chars
#         "\t\n\r\f\v",                      # Whitespace chars
#         "\x00\x01\x02\x03\x04\x05",        # Control chars
#         "'\""                               # Quotes
#     ]
#
#     for s in special_strings:
#         assert field.validate_and_build(s) == s
