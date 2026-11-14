"""Tests for mini_html5_named_entity.

These exercise the behaviour the library actually claims: full named set with
semicolons, legacy no-semicolon forms, the HTML5 rule that a legacy name is
not consumed when followed by '=' or an alphanumeric, and pass-through of
unknown or numeric references.
"""

import unittest

from mini_html5_named_entity import decode, decode_bytes


class TestDecodeBasics(unittest.TestCase):
    def test_plain_text_unchanged(self):
        self.assertEqual(decode("hello world"), "hello world")

    def test_empty_string(self):
        self.assertEqual(decode(""), "")

    def test_semicolon_forms(self):
        self.assertEqual(decode("&amp;"), "&")
        self.assertEqual(decode("&lt;&gt;"), "<>")
        self.assertEqual(decode("&copy;"), "\u00a9")
        self.assertEqual(decode("&nbsp;"), "\u00a0")

    def test_multiple_references(self):
        self.assertEqual(decode("a &amp; b &lt; c"), "a & b < c")

    def test_adjacent_references(self):
        self.assertEqual(decode("&amp;&lt;&gt;"), "&<>")

    def test_unknown_reference_passthrough(self):
        self.assertEqual(decode("&notarealentity;"), "&notarealentity;")
        self.assertEqual(decode("&;"), "&;")
        self.assertEqual(decode("&"), "&")

    def test_bare_ampersand(self):
        self.assertEqual(decode("a & b"), "a & b")

    def test_numeric_references_untouched(self):
        # The library deliberately does not handle numeric references.
        self.assertEqual(decode("&#65;"), "&#65;")
        self.assertEqual(decode("&#x41;"), "&#x41;")


class TestLegacyNoSemicolon(unittest.TestCase):
    def test_simple_legacy(self):
        self.assertEqual(decode("&amp"), "&")
        self.assertEqual(decode("&copy"), "\u00a9")
        self.assertEqual(decode("&lt"), "<")

    def test_legacy_followed_by_space(self):
        self.assertEqual(decode("&amp rest"), "& rest")

    def test_legacy_followed_by_punctuation(self):
        self.assertEqual(decode("&amp!"), "&!")
        self.assertEqual(decode("&amp."), "&.")

    def test_legacy_followed_by_equals_is_literal(self):
        # HTML5 rule: a legacy name followed by '=' is not a reference.
        self.assertEqual(decode("&amp=1"), "&amp=1")
        self.assertEqual(decode("&copy=2"), "&copy=2")

    def test_legacy_followed_by_alnum_is_literal(self):
        # HTML5 rule: a legacy name followed by an alphanumeric is not a
        # reference, because the tokenizer would keep consuming the name.
        self.assertEqual(decode("&ampx"), "&ampx")
        self.assertEqual(decode("&copy1"), "&copy1")

    def test_semicolon_form_always_wins(self):
        self.assertEqual(decode("&amp;x"), "&x")
        self.assertEqual(decode("&amp;"), "&")

    def test_longest_match_wins(self):
        # '&notin;' is a longer name than '&not'. With a semicolon the
        # canonical form must win.
        self.assertEqual(decode("&notin;"), "\u2209")
        # Without a semicolon, '&not' is the legacy form and 'in' follows as
        # literal text, but 'in' is alphanumeric so the legacy form is NOT
        # consumed; the whole thing stays literal.
        self.assertEqual(decode("&notin"), "&notin")


class TestDecodeBytes(unittest.TestCase):
    def test_utf8_roundtrip(self):
        self.assertEqual(decode_bytes(b"&amp;"), b"&")

    def test_utf8_multibyte(self):
        self.assertEqual(decode_bytes("caf\u00e9 &amp; tea".encode("utf-8")), "caf\u00e9 & tea".encode("utf-8"))

    def test_latin1(self):
        # '\u00e9' encodes to a single byte in latin-1.
        self.assertEqual(decode_bytes(b"&copy; \xe9", encoding="latin-1"), b"\xa9 \xe9")

    def test_bytearray_accepted(self):
        self.assertEqual(decode_bytes(bytearray(b"&lt;")), b"<")

    def test_type_error_on_str(self):
        with self.assertRaises(TypeError):
            decode_bytes("&amp;")  # type: ignore[arg-type]


class TestTypeErrors(unittest.TestCase):
    def test_decode_requires_str(self):
        with self.assertRaises(TypeError):
            decode(b"&amp;")  # type: ignore[arg-type]


class TestEdgeCases(unittest.TestCase):
    def test_ampersand_at_end(self):
        self.assertEqual(decode("trailing &"), "trailing &")

    def test_double_ampersand(self):
        self.assertEqual(decode("&&amp;"), "&&")

    def test_legacy_at_end_of_string(self):
        self.assertEqual(decode("x&amp"), "x&")

    def test_semicolon_alone(self):
        self.assertEqual(decode(";"), ";")

    def test_unicode_passthrough(self):
        self.assertEqual(decode("\u00e9&amp;\u00e9"), "\u00e9&\u00e9")

    def test_all_semicolon_entries_decode(self):
        # Sanity check that every key in the table is reachable through the
        # public API. This is not a correctness proof of the values, but it
        # catches accidental key typos that would make an entry unreachable.
        from mini_html5_named_entity.core import NAMED_ENTITIES

        for name in NAMED_ENTITIES:
            if name.endswith(";"):
                self.assertEqual(
                    decode(name),
                    NAMED_ENTITIES[name],
                    "failed to decode %r" % name,
                )


if __name__ == "__main__":
    unittest.main()
