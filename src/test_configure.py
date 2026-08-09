#!/usr/bin/env python3
"""Direct-function tests for configure.py's pure logic -- previously
untested entirely (no test file for this module existed). configure.py
imports streamlit at module level, so this whole file is skipped (not
failed) when it's not installed -- the stdlib-only core suite must stay
runnable without the venv (see test_mcp_server.py for the same pattern).

Most of configure.py is Streamlit rendering, not unit-testable without a
full AppTest harness -- these are the pieces that are plain functions
first and Streamlit calls second.

Run with (needs the venv -- see README's MCP setup section):
    cd src && ../.venv/bin/python3 -m unittest test_configure -v
"""
import unittest

try:
    import configure
    _STREAMLIT_AVAILABLE = True
except ImportError:
    _STREAMLIT_AVAILABLE = False


@unittest.skipUnless(_STREAMLIT_AVAILABLE, "streamlit not installed -- see README's MCP setup section")
class SyntheticPathForGlobTests(unittest.TestCase):
    """Feeds "Try it" and any pack/context resolution downstream, which
    need a concrete path to fnmatch against, not a pattern -- see
    core.config.matching_rule and core.config.packs_for_path, both keyed
    on a real relative path."""

    def test_literal_glob_passes_through_unchanged(self):
        self.assertEqual(configure._synthetic_path_for_glob("README.md"), "README.md")

    def test_suffix_wildcard_gets_a_stand_in_stem(self):
        result = configure._synthetic_path_for_glob("*.md")
        self.assertEqual(result, "__probe__.md")

    def test_wildcard_inside_a_directory_segment(self):
        result = configure._synthetic_path_for_glob("docs/security/*.md")
        self.assertEqual(result, "docs/security/__probe__.md")

    def test_bare_wildcard_directory_segment(self):
        result = configure._synthetic_path_for_glob(".claude/*")
        self.assertEqual(result, ".claude/__probe__")

    def test_result_actually_matches_the_source_glob(self):
        import fnmatch
        for glob in ("README.md", "*.md", "*.txt", "docs/security/*.md", ".claude/*"):
            with self.subTest(glob=glob):
                self.assertTrue(fnmatch.fnmatch(
                    configure._synthetic_path_for_glob(glob), glob))


@unittest.skipUnless(_STREAMLIT_AVAILABLE, "streamlit not installed -- see README's MCP setup section")
class PackCountTests(unittest.TestCase):

    def test_no_packs_key_counts_as_zero(self):
        self.assertEqual(configure._pack_count({"glob": "*.py"}), 0)

    def test_sums_across_every_list(self):
        rule = {"packs": {"project_terms": ["a", "b"], "other_list": ["c"]}}
        self.assertEqual(configure._pack_count(rule), 3)


@unittest.skipUnless(_STREAMLIT_AVAILABLE, "streamlit not installed -- see README's MCP setup section")

@unittest.skipUnless(_STREAMLIT_AVAILABLE, "streamlit not installed -- see README's MCP setup section")
class CheckConfigEditsTests(unittest.TestCase):
    """The checks table writes what this function says changed, so a
    false positive here is a config write nobody asked for, and a false
    negative is an edit that silently does not save.

    st.data_editor cannot report which cell moved -- it returns the whole
    table -- so the diff IS the change detection, and it runs on EVERY
    rerun, including reruns nothing to do with this table (a Path change,
    an Undo). "No edit" therefore has to be the reliable case, not the
    lucky one. The threshold/action columns are dense on every row, so a
    change is keyed by check id, never by a shared option name."""

    def _rows(self, *checks):
        return [{"check": c} for c in checks]

    def test_an_untouched_table_writes_nothing(self):
        rows = self._rows("em_dash_cluster", "vague_intensifier")
        table = [{"on": True, "threshold": 4, "action": "block"},
                 {"on": True, "threshold": 1, "action": "warn"}]
        toggles, changes, error = configure.check_config_edits(
            rows, table, [dict(r) for r in table])
        self.assertEqual((toggles, changes, error), ({}, {}, None))

    def test_a_toggled_check_is_reported_by_its_own_id(self):
        rows = self._rows("em_dash_cluster", "vague_intensifier")
        before = [{"on": True, "threshold": 4, "action": "block"},
                  {"on": True, "threshold": 1, "action": "warn"}]
        after = [{"on": False, "threshold": 4, "action": "block"},
                 {"on": True, "threshold": 1, "action": "warn"}]
        toggles, changes, _ = configure.check_config_edits(rows, before, after)
        self.assertEqual(toggles, {"em_dash_cluster": False})
        self.assertEqual(changes, {})

    def test_a_changed_threshold_is_reported_under_its_own_check(self):
        rows = self._rows("vague_intensifier")
        before = [{"on": True, "threshold": 1, "action": "warn"}]
        after = [{"on": True, "threshold": 3, "action": "warn"}]
        _toggles, changes, error = configure.check_config_edits(rows, before, after)
        self.assertEqual(changes, {"vague_intensifier": {"threshold": 3}})
        self.assertIsNone(error)

    def test_a_changed_action_is_reported_under_its_own_check(self):
        rows = self._rows("vague_intensifier")
        before = [{"on": True, "threshold": 1, "action": "warn"}]
        after = [{"on": True, "threshold": 1, "action": "block"}]
        _toggles, changes, error = configure.check_config_edits(rows, before, after)
        self.assertEqual(changes, {"vague_intensifier": {"action": "block"}})
        self.assertIsNone(error)

    def test_both_fields_changing_on_one_row_report_together(self):
        rows = self._rows("vague_intensifier")
        before = [{"on": True, "threshold": 1, "action": "warn"}]
        after = [{"on": True, "threshold": 5, "action": "block"}]
        _toggles, changes, error = configure.check_config_edits(rows, before, after)
        self.assertEqual(changes, {"vague_intensifier": {"threshold": 5, "action": "block"}})
        self.assertIsNone(error)

    def test_a_cleared_threshold_is_left_alone_not_an_error(self):
        """Every row has a real threshold (the column is dense, never
        sparse) -- a cleared cell reverts on the next rerun rather than
        writing "no threshold", which has no meaning here."""
        rows = self._rows("vague_intensifier")
        before = [{"on": True, "threshold": 1, "action": "warn"}]
        after = [{"on": True, "threshold": None, "action": "warn"}]
        _toggles, changes, error = configure.check_config_edits(rows, before, after)
        self.assertEqual(changes, {})
        self.assertIsNone(error)

    def test_a_threshold_below_one_is_rejected(self):
        rows = self._rows("vague_intensifier")
        before = [{"on": True, "threshold": 1, "action": "warn"}]
        after = [{"on": True, "threshold": 0, "action": "warn"}]
        toggles, changes, error = configure.check_config_edits(rows, before, after)
        self.assertEqual((toggles, changes), ({}, {}))
        self.assertIn("at least 1", error)

    def test_nonsense_threshold_reports_an_error_and_writes_nothing(self):
        rows = self._rows("passive", "vague_intensifier")
        before = [{"on": True, "threshold": 4, "action": "block"},
                  {"on": True, "threshold": 1, "action": "warn"}]
        after = [{"on": False, "threshold": 4, "action": "block"},
                 {"on": True, "threshold": "many", "action": "warn"}]
        toggles, changes, error = configure.check_config_edits(rows, before, after)
        self.assertEqual((toggles, changes), ({}, {}))
        self.assertIn("whole number", error)


if __name__ == "__main__":
    unittest.main()
