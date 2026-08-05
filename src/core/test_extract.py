"""core/extract.py: the prose-embedded-in-code pass.

Extraction is the risky half -- a wrong segment set either lints
plumbing strings (noise on every write) or misses the UI copy this
exists to reach (the gate quietly off). The gating half is pooling
logic, tested against a stub ruleset so no real ruleset's checks leak
into these assertions.
"""
import types
import unittest

from core import extract


class ProseSegmentsTests(unittest.TestCase):

    def _lines(self, source):
        return [s["line"] for s in extract.prose_segments(source, ".py")]

    def test_a_sentence_sized_string_is_extracted_with_its_line(self):
        source = 'x = 1\nmsg = "This sentence has five words."\n'
        segments = extract.prose_segments(source, ".py")
        self.assertEqual(segments,
                          [{"line": 2, "text": "This sentence has five words."}])

    def test_short_strings_are_plumbing_not_prose(self):
        # Keys, paths, format specs: all real string literals, none of
        # them prose. The word-count floor is what keeps them out.
        source = ('a = "block_flag_count_threshold"\n'
                  'b = "%Y-%m-%d %H:%M:%S"\n'
                  'c = "two words"\nd = "only three words"\n')
        self.assertEqual(extract.prose_segments(source, ".py"), [])

    def test_a_docstring_is_a_constant_like_any_other(self):
        source = 'def f():\n    """Say the one important thing."""\n'
        self.assertEqual(self._lines(source), [2])

    def test_fstring_parts_join_into_one_segment_with_stand_ins(self):
        source = 'msg = f"{n} checks run on {probe} today"\n'
        segments = extract.prose_segments(source, ".py")
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0]["text"],
                          f"{extract.STAND_IN} checks run on {extract.STAND_IN} today")

    def test_fstring_constants_are_not_also_reported_alone(self):
        # The constant pieces of a JoinedStr are ast.Constant nodes too;
        # a naive walk yields each twice -- once joined, once bare.
        source = 'msg = f"a long enough constant piece here {x}"\n'
        self.assertEqual(len(extract.prose_segments(source, ".py")), 1)

    def test_implicit_concatenation_is_one_segment(self):
        source = 'msg = ("first half of a sentence "\n        "and its second half")\n'
        segments = extract.prose_segments(source, ".py")
        self.assertEqual(len(segments), 1)
        self.assertIn("first half", segments[0]["text"])
        self.assertIn("second half", segments[0]["text"])

    def test_bytes_are_not_prose(self):
        self.assertEqual(
            extract.prose_segments('x = b"four words of bytes"\n', ".py"), [])

    def test_broken_source_yields_nothing_rather_than_raising(self):
        # A half-written draft must never crash the gate.
        self.assertEqual(extract.prose_segments("def broken(:\n", ".py"), [])

    def test_unsupported_extension_yields_nothing(self):
        self.assertEqual(
            extract.prose_segments('"real prose with many words"', ".js"), [])


def _stub_ruleset(threshold):
    """A minimal embedded ruleset: every word spelled 'slop' flags, and
    the deny policy is a bare count threshold."""
    def lint_and_gate(text, file_path=None):
        flags = [{"kind": "stub_slop", "detail": {}, "label": w}
                 for w in text.split() if w == "slop"]
        return {"semantic_flags": flags, "mechanical_violations": []}

    def blocking_semantic_flags(flags):
        return flags if len(flags) >= threshold else []

    return types.SimpleNamespace(lint_and_gate=lint_and_gate,
                                  blocking_semantic_flags=blocking_semantic_flags)


class EmbeddedProseFlagsTests(unittest.TestCase):

    SOURCE = ('a = "slop in the first string"\n'
              'b = "slop in the second string"\n')

    def test_flags_pool_across_segments_before_the_policy_runs(self):
        # One flag per segment; a per-segment threshold of 2 would let
        # both through. Pooling is the point: density is judged over the
        # file's whole embedded prose.
        flags = extract.embedded_prose_flags(self.SOURCE, ".py", _stub_ruleset(2))
        self.assertEqual(len(flags), 2)

    def test_below_the_pooled_threshold_nothing_blocks(self):
        flags = extract.embedded_prose_flags(self.SOURCE, ".py", _stub_ruleset(3))
        self.assertEqual(flags, [])

    def test_each_flag_carries_its_segment_line(self):
        flags = extract.embedded_prose_flags(self.SOURCE, ".py", _stub_ruleset(1))
        self.assertEqual(sorted(f["embedded_line"] for f in flags), [1, 2])

    def test_no_segments_means_no_ruleset_calls_at_all(self):
        def explode(*a, **k):
            raise AssertionError("ruleset called with nothing to judge")
        module = types.SimpleNamespace(lint_and_gate=explode,
                                        blocking_semantic_flags=lambda f: f)
        self.assertEqual(
            extract.embedded_prose_flags("x = 1\n", ".py", module), [])


class RuleEmbeddedRulesetTests(unittest.TestCase):

    def _registry(self):
        class Unknown(Exception):
            pass
        return types.SimpleNamespace(
            UnknownRulesetError=Unknown,
            get_ruleset=lambda rid: {"slopwatch": "MODULE"}.get(rid)
                        or (_ for _ in ()).throw(Unknown(rid)))

    def test_a_rule_without_the_key_yields_none(self):
        self.assertIsNone(extract.rule_embedded_ruleset(
            {"glob": "*.py", "ruleset": "codewatch"}, self._registry()))
        self.assertIsNone(extract.rule_embedded_ruleset(None, self._registry()))

    def test_a_typo_is_loud_not_silent(self):
        registry = self._registry()
        with self.assertRaises(registry.UnknownRulesetError):
            extract.rule_embedded_ruleset(
                {"glob": "*.py", "embedded_prose": "slopwtch"}, registry)


class GlobExtensionSupportTests(unittest.TestCase):

    def test_supported_and_unsupported_extensions(self):
        self.assertTrue(extract.glob_extension_supported("*.py"))
        self.assertFalse(extract.glob_extension_supported("*.js"))
        self.assertFalse(extract.glob_extension_supported("README.md"))

    def test_no_extension_defers_to_the_per_file_check(self):
        self.assertTrue(extract.glob_extension_supported(".claude/*"))


if __name__ == "__main__":
    unittest.main()
