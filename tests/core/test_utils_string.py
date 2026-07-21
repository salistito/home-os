import pytest

from core.utils.string import html_escape, normalize_string


@pytest.mark.unit
class TestNormalizeString:
    def test_collapses_multiple_spaces(self):
        assert normalize_string("  hello   world  ") == "Hello world"

    def test_strips_leading_and_trailing(self):
        assert normalize_string("  hello  ") == "Hello"

    def test_single_word(self):
        assert normalize_string("single") == "Single"

    def test_uppercases_first_letter(self):
        assert normalize_string("HELLO WORLD") == "Hello world"

    def test_lowercases_rest(self):
        assert normalize_string("hELLO wORLD") == "Hello world"

    def test_all_uppercase(self):
        assert normalize_string("ALL CAPS") == "All caps"

    def test_already_normalized(self):
        assert normalize_string("Hello world") == "Hello world"

    def test_empty_string(self):
        assert normalize_string("") == ""

    def test_whitespace_only(self):
        assert normalize_string("   ") == ""

    def test_tabs_and_newlines(self):
        assert normalize_string("\thello\nworld\n") == "Hello world"

    def test_mixed_whitespace(self):
        assert normalize_string(" \t hello \n world \t ") == "Hello world"

    def test_single_character(self):
        assert normalize_string("a") == "A"

    def test_single_letter_words(self):
        assert normalize_string("a b c") == "A b c"

    def test_unicode_text(self):
        assert normalize_string("  español  ") == "Español"

    def test_numbers_preserved(self):
        assert normalize_string("  item 42  ") == "Item 42"


@pytest.mark.unit
class TestHtmlEscape:
    def test_escapes_lt(self):
        assert html_escape("a < b") == "a &lt; b"

    def test_escapes_ampersand(self):
        assert html_escape("a & b") == "a &amp; b"

    def test_escapes_gt(self):
        assert html_escape("a > b") == "a &gt; b"

    def test_escapes_all_together(self):
        assert html_escape("a < b & c") == "a &lt; b &amp; c"

    def test_normal_text_unchanged(self):
        assert html_escape("normal") == "normal"

    def test_empty_string(self):
        assert html_escape("") == ""

    def test_text_with_quotes(self):
        result = html_escape('say "hello"')
        assert "&quot;" in result

    def test_text_with_single_quotes(self):
        result = html_escape("it's")
        assert "&#x27;" in result

    def test_multiple_special_chars(self):
        assert html_escape("a && b << c") == "a &amp;&amp; b &lt;&lt; c"

    def test_numbers_unchanged(self):
        assert html_escape("123") == "123"

    def test_unicode_preserved(self):
        assert html_escape("café") == "café"
