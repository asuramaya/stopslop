#!/usr/bin/env python3
"""Importing another project's rules.

The rule that matters here is refuse-never-guess. A Vale rule this
importer cannot represent faithfully must be refused BY NAME, not
approximated into a check that fires on something else, because nothing
downstream ever questions an imported check again.
"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import vale_import

EXISTENCE = """extends: existence
message: "Cliche '%s': cut it or say the literal thing."
level: suggestion
ignorecase: true
tokens:
  - 'game[ -]changer'
  - 'low-hanging fruit'
"""

RAW = """extends: existence
message: "'not just X, but Y' escalation: say Y."
level: suggestion
ignorecase: true
raw:
  - '\\bnot\\s+(?:just|only)\\b'
  - '|\\bisn[''’]?t\\s+just\\b'
"""

NONWORD = """extends: existence
message: "Em/en dash: recast it."
level: error
nonword: true
tokens:
  - '—'
"""


class ConvertTests(unittest.TestCase):
    def test_tokens_become_a_word_bounded_alternation(self):
        spec = vale_import.convert(EXISTENCE, "Cliche")
        self.assertEqual(spec["check_id"], "vale_cliche")
        self.assertIn("game[ -]changer|low-hanging fruit", spec["fn_body"])
        self.assertIn(r"\b(?:", spec["fn_body"])

    def test_nonword_drops_the_word_boundaries(self):
        """An em dash has no word boundary. Keeping \\b would make the
        rule silently never fire, which is worse than refusing it."""
        spec = vale_import.convert(NONWORD, "Dash")
        self.assertNotIn(r"\b(?:", spec["fn_body"])

    def test_raw_entries_concatenate_rather_than_alternate(self):
        """Vale joins raw entries, which is why rules in the wild open
        later entries with '|'. Alternating them here would build a
        different regex from the one the author tested -- so this checks
        the generated matcher's BEHAVIOUR, since only the second raw
        entry can match the "isn't just" form."""
        check = self._compile(vale_import.convert(RAW, "NegParallel"))
        self.assertTrue(check("this is not just fast"))
        self.assertTrue(check("it isn't just fast"))
        self.assertEqual(check("nothing here"), [])

    def _compile(self, spec):
        namespace = {}
        source = "def check(sentence, extra=()):\n" + "\n".join(
            "    " + line for line in spec["fn_body"].splitlines())
        exec(compile(source, "<generated>", "exec"), namespace)
        return namespace["check"]

    def test_vale_error_becomes_a_blocking_check(self):
        self.assertEqual(vale_import.convert(NONWORD, "Dash")["action"], "block")

    def test_vale_suggestion_becomes_a_warning(self):
        self.assertEqual(vale_import.convert(EXISTENCE, "Cliche")["action"],
                          "warn")

    def test_the_message_splits_into_catches_and_instead(self):
        spec = vale_import.convert(EXISTENCE, "Cliche")
        self.assertEqual(spec["instead"], "cut it or say the literal thing.")
        self.assertNotIn("%s", spec["catches"])

    def test_ignorecase_reaches_the_generated_matcher(self):
        self.assertIn("re.IGNORECASE",
                       vale_import.convert(EXISTENCE, "Cliche")["fn_body"])
        self.assertNotIn("re.IGNORECASE",
                          vale_import.convert(NONWORD, "Dash")["fn_body"])

    def test_the_generated_body_is_real_runnable_python(self):
        check = self._compile(vale_import.convert(EXISTENCE, "Cliche"))
        self.assertTrue(check("a real game-changer here"))
        self.assertEqual(check("nothing to see"), [])

    def test_a_camel_case_name_becomes_a_snake_case_id(self):
        self.assertEqual(vale_import.check_id_for("AbstractTriad"),
                          "vale_abstract_triad")


class RefusalTests(unittest.TestCase):
    def test_an_unsupported_extends_is_refused_by_name(self):
        with self.assertRaises(vale_import.UnsupportedRule) as caught:
            vale_import.convert("extends: substitution\nmessage: 'x'\n", "Swap")
        self.assertIn("substitution", str(caught.exception))

    def test_a_rule_with_no_pattern_is_refused(self):
        with self.assertRaises(vale_import.UnsupportedRule):
            vale_import.convert("extends: existence\nmessage: 'x'\n", "Empty")

    def test_a_pattern_that_does_not_compile_is_refused(self):
        broken = "extends: existence\nmessage: 'x'\nraw:\n  - '([unclosed'\n"
        with self.assertRaises(vale_import.UnsupportedRule):
            vale_import.convert(broken, "Broken")

    def test_an_unknown_level_is_refused_rather_than_defaulted(self):
        """Defaulting an unknown severity would silently decide whether
        someone's rule blocks a write."""
        text = EXISTENCE.replace("level: suggestion", "level: catastrophe")
        with self.assertRaises(vale_import.UnsupportedRule):
            vale_import.convert(text, "Cliche")

    def test_an_unknown_field_is_refused_rather_than_ignored(self):
        text = EXISTENCE + "exceptions:\n  - 'ok'\n"
        with self.assertRaises(vale_import.UnsupportedRule):
            vale_import.convert(text, "Cliche")


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def _write(self, name, text):
        with open(os.path.join(self.dir, name), "w") as f:
            f.write(text)

    def test_it_reports_refusals_beside_imports_never_silently(self):
        """A partial import that hides its own gaps is how someone comes
        to believe they are covered when they are not."""
        self._write("Cliche.yml", EXISTENCE)
        self._write("Swap.yml", "extends: substitution\nmessage: 'x'\n")
        converted, refused = vale_import.read_package(self.dir)
        self.assertEqual([c["check_id"] for c in converted], ["vale_cliche"])
        self.assertEqual(len(refused), 1)
        self.assertEqual(refused[0][0], "Swap")

    def test_non_yaml_files_are_left_alone(self):
        self._write("Cliche.yml", EXISTENCE)
        self._write("README.md", "not a rule")
        converted, refused = vale_import.read_package(self.dir)
        self.assertEqual(len(converted), 1)
        self.assertEqual(refused, [])

    def test_a_missing_directory_raises(self):
        with self.assertRaises(FileNotFoundError):
            vale_import.read_package(os.path.join(self.dir, "nope"))

    def test_the_prefix_is_configurable_so_two_packages_can_coexist(self):
        self._write("Cliche.yml", EXISTENCE)
        converted, _ = vale_import.read_package(self.dir, prefix="aitells")
        self.assertEqual(converted[0]["check_id"], "aitells_cliche")


if __name__ == "__main__":
    unittest.main()
