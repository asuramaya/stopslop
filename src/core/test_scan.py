#!/usr/bin/env python3
"""Tests for core/scan.py's bulk-scan-a-tree helper.

Uses a tiny fake ruleset (flags any file whose content contains the literal
string "BADWORD") so these tests exercise scan_tree's own walking/
resolution/skip logic, not any real ruleset's rules.
"""
import os
import shutil
import tempfile
import types
import unittest

from core import paths as core_paths
from core import scan
import rulesets

REPO_ROOT = core_paths.find_project_root(__file__)


def _fake_ruleset(ruleset_id="fake"):
    mod = types.SimpleNamespace()
    mod.RULESET_ID = ruleset_id

    def lint_and_gate(text, context=None, file_path=None):
        semantic = [{"kind": "badword", "label": "BADWORD", "detail": {"rule": "fake.badword"}}] \
            if "BADWORD" in text else []
        mechanical = [{"kind": "trailing_space", "label": "  ", "detail": {"rule": "fake.trailing_space"}}] \
            if text.endswith("  \n") else []
        return {"semantic_flags": semantic, "mechanical_violations": mechanical}

    mod.lint_and_gate = lint_and_gate
    mod.blocking_semantic_flags = lambda flags: flags  # every semantic flag blocks, for this fake
    return mod


class _FakeRegistry:
    def __init__(self, *rulesets_):
        self._by_id = {r.RULESET_ID: r for r in rulesets_}

    def get_ruleset(self, ruleset_id):
        try:
            return self._by_id[ruleset_id]
        except KeyError:
            raise rulesets.UnknownRulesetError(ruleset_id)


class ScanTreeForcedRulesetTests(unittest.TestCase):
    """ruleset_id="fake" -- every matched file goes through one forced
    ruleset regardless of any config, the mode that lets a project test a
    ruleset against files it isn't routed to lint yet."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        self.registry = _FakeRegistry(_fake_ruleset())

    def tearDown(self):
        self.tmp.cleanup()

    def _write(self, rel_path, content, binary=False):
        full = os.path.join(self.root, rel_path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        mode = "wb" if binary else "w"
        with open(full, mode) as f:
            f.write(content)
        return full

    def test_flags_a_file_with_the_bad_pattern(self):
        self._write("a.txt", "this has BADWORD in it")
        self._write("b.txt", "this is clean")
        report = scan.scan_tree([self.root], self.root, self.registry, ruleset_id="fake")
        self.assertEqual(report["scanned"], 2)
        blocked = [r for r in report["results"] if r["would_block"]]
        self.assertEqual(len(blocked), 1)
        self.assertTrue(blocked[0]["path"].endswith("a.txt"))

    def test_glob_pattern_narrows_forced_mode(self):
        self._write("a.py", "BADWORD")
        self._write("a.md", "BADWORD")
        report = scan.scan_tree([self.root], self.root, self.registry,
                                 ruleset_id="fake", glob_pattern="*.py")
        self.assertEqual(report["scanned"], 1)
        self.assertTrue(report["results"][0]["path"].endswith("a.py"))

    def test_skips_known_junk_dirs(self):
        self._write("real.txt", "BADWORD")
        self._write(os.path.join("__pycache__", "cached.txt"), "BADWORD")
        self._write(os.path.join(".git", "objects", "x.txt"), "BADWORD")
        self._write(os.path.join("node_modules", "pkg", "x.txt"), "BADWORD")
        report = scan.scan_tree([self.root], self.root, self.registry, ruleset_id="fake")
        self.assertEqual(report["scanned"], 1)

    def test_other_dot_dirs_stay_walkable(self):
        # Only the explicit junk-dir list is non-negotiable -- a dot-dir
        # that isn't on it (e.g. a docs-hosting convention like .github/)
        # must still be reachable in forced mode.
        self._write(os.path.join(".github", "CONTRIBUTING.md"), "BADWORD")
        report = scan.scan_tree([self.root], self.root, self.registry, ruleset_id="fake")
        self.assertEqual(report["scanned"], 1)

    def test_skips_unreadable_binary_file(self):
        self._write("bin.dat", b"\xff\xfe\x00\x01BADWORD\xff", binary=True)
        report = scan.scan_tree([self.root], self.root, self.registry, ruleset_id="fake")
        self.assertEqual(report["scanned"], 0)
        self.assertEqual(report["skipped_unreadable"], 1)

    def test_skips_empty_file(self):
        self._write("empty.txt", "   \n")
        report = scan.scan_tree([self.root], self.root, self.registry, ruleset_id="fake")
        self.assertEqual(report["scanned"], 0)

    def test_single_file_path_input(self):
        path = self._write("only.txt", "BADWORD")
        report = scan.scan_tree([path], self.root, self.registry, ruleset_id="fake")
        self.assertEqual(report["scanned"], 1)
        self.assertTrue(report["results"][0]["would_block"])

    def test_mechanical_only_flags_do_not_block(self):
        self._write("m.txt", "clean text with trailing space  \n")
        report = scan.scan_tree([self.root], self.root, self.registry, ruleset_id="fake")
        self.assertEqual(report["scanned"], 1)
        r = report["results"][0]
        self.assertFalse(r["would_block"])
        self.assertEqual(len(r["mechanical_flags"]), 1)

    def test_unknown_forced_ruleset_id_raises_loudly(self):
        with self.assertRaises(rulesets.UnknownRulesetError):
            scan.scan_tree([self.root], self.root, self.registry, ruleset_id="typo-name")


class ScanTreeConfigDrivenTests(unittest.TestCase):
    """ruleset_id=None resolves each file through core.config, same path
    resolution a live write uses -- exercised against the real config
    module (not a fake) so this proves scan.py's own resolution call
    matches what the live gate would actually do."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        self.registry = _FakeRegistry(_fake_ruleset("ste100"))

    def tearDown(self):
        self.tmp.cleanup()

    def _write(self, rel_path, content):
        full = os.path.join(self.root, rel_path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w") as f:
            f.write(content)
        return full

    def test_default_rules_only_scans_md_txt_rst(self):
        # Only the "which extensions are in scope at all" shape: prose in,
        # everything else out. Which ruleset prose routes to is the next
        # test's job.
        self._write("guide.md", "BADWORD")
        self._write("data.json", "BADWORD")
        self._write("notes.txt", "BADWORD")
        registry = _FakeRegistry(_fake_ruleset("slopwatch"))
        report = scan.scan_tree([self.root], self.root, registry,
                                 config_file="/nonexistent/stopslop.config.json")
        self.assertEqual(report["scanned"], 2)
        self.assertEqual(report["skipped_out_of_scope"], 1)
        scanned_names = {os.path.basename(r["path"]) for r in report["results"]}
        self.assertEqual(scanned_names, {"guide.md", "notes.txt"})

    def test_default_rules_route_prose_to_slopwatch_and_py_to_codewatch(self):
        registry = _FakeRegistry(_fake_ruleset("ste100"), _fake_ruleset("slopwatch"),
                                  _fake_ruleset("codewatch"))
        self._write("README.md", "BADWORD")
        self._write("script.py", "BADWORD")
        self._write(os.path.join("docs", "README.md"), "BADWORD")  # nested -- not "the" README
        report = scan.scan_tree([self.root], self.root, registry,
                                 config_file="/nonexistent/stopslop.config.json")
        # Keyed on the path relative to self.root, not basename -- the root
        # and nested README.md share a basename and would otherwise clobber
        # each other in the lookup.
        by_relpath = {os.path.relpath(r["path"], self.root): r["ruleset"] for r in report["results"]}
        self.assertEqual(by_relpath["README.md"], "slopwatch")
        self.assertEqual(by_relpath["script.py"], "codewatch")
        # A nested README is prose like any other .md -- there is no longer
        # a special case for depth, because there is no longer a second
        # prose ruleset for it to fall through to.
        self.assertEqual(by_relpath[os.path.join("docs", "README.md")], "slopwatch")

    def test_claude_dir_counts_as_out_of_scope_not_invisible(self):
        self._write(os.path.join(".claude", "notes.md"), "BADWORD")
        report = scan.scan_tree([self.root], self.root, self.registry,
                                 config_file="/nonexistent/stopslop.config.json")
        self.assertEqual(report["scanned"], 0)
        self.assertEqual(report["skipped_out_of_scope"], 1)

    def test_custom_config_routes_a_dot_dir_the_walker_would_otherwise_skip(self):
        import json
        # Config lives OUTSIDE the scanned root -- otherwise the config
        # file itself would be swept up as one more (out-of-scope) file,
        # muddying the count this test is actually checking.
        with tempfile.TemporaryDirectory() as config_dir:
            config_path = os.path.join(config_dir, "stopslop.config.json")
            with open(config_path, "w") as f:
                json.dump({"rulesets": [{"glob": ".github/*.md", "ruleset": "ste100"}]}, f)
            self._write(os.path.join(".github", "CONTRIBUTING.md"), "BADWORD")
            report = scan.scan_tree([self.root], self.root, self.registry, config_file=config_path)
        self.assertEqual(report["scanned"], 1)
        self.assertEqual(report["skipped_out_of_scope"], 0)


if __name__ == "__main__":
    unittest.main()


class CheckActivityTests(unittest.TestCase):
    """The question no other tool in this category can ask: which checks
    did NOT fire.

    A check that never fires is invisible precisely because absence
    produces no output. Measured across 59902 words of this project's own
    saved model output, 19 of slopwatch's 31 checks fired zero times.
    """

    def setUp(self):
        self.ruleset = rulesets.get_ruleset("slopwatch")
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir)

    def _write(self, name, text):
        path = os.path.join(self.dir, name)
        with open(path, "w") as f:
            f.write(text)
        return path

    def _activity(self):
        report = scan.scan_tree([self.dir], REPO_ROOT, rulesets,
                                 ruleset_id="slopwatch")
        return scan.check_activity(report, self.ruleset)

    def test_every_check_appears_including_the_silent_ones(self):
        """Reporting only what fired is what hides a decayed check set."""
        self._write("a.md", "The cache stores query results on disk.\n")
        summary = self._activity()
        self.assertEqual(set(summary["activity"]),
                          set(self.ruleset.list_checks()))

    def test_a_check_that_never_fires_reports_zero_not_absence(self):
        self._write("a.md", "The cache stores query results on disk.\n")
        for entry in self._activity()["activity"].values():
            self.assertIn("hits", entry)
            self.assertIn("per_1k", entry)

    def test_hits_and_files_are_counted_separately(self):
        """Three hits in one document is not the same evidence as one hit
        in three documents, and a single number cannot tell them apart."""
        self._write("a.md", "Needless to say, this is seamless.\n"
                             "Needless to say, it is also robust.\n")
        summary = self._activity()
        fired = [e for e in summary["activity"].values() if e["hits"]]
        self.assertTrue(fired)
        self.assertTrue(any(e["hits"] > e["files"] for e in fired))

    def test_the_rate_is_per_thousand_words_of_the_whole_corpus(self):
        self._write("a.md", " ".join(["word"] * 1000) + "\nseamless robust.\n")
        summary = self._activity()
        self.assertGreater(summary["words"], 1000)
        total = sum(e["per_1k"] for e in summary["activity"].values())
        self.assertLess(total, 100)

    def test_an_empty_corpus_reports_no_documents_rather_than_dividing(self):
        summary = self._activity()
        self.assertEqual(summary["documents"], 0)
        self.assertEqual(summary["words"], 0)
        for entry in summary["activity"].values():
            self.assertEqual(entry["per_1k"], 0.0)


class CompareActivityTests(unittest.TestCase):
    """Whether a check detects a machine, or only a style.

    A check that fires equally on human prose is not a tell. Enforcing it
    moves writing AWAY from the human distribution rather than toward it,
    which is the opposite of what the gate is for. Measured against 32565
    words of CPython stdlib docstrings and package documentation,
    colon_reveal -- the second highest-firing check in slopwatch and one
    the harness ENFORCES -- scored 2.84 per 1000 words on generated text
    and 2.76 on human text.
    """

    def _corpus(self, rates, words=1000):
        return {"activity": {k: {"per_1k": v, "hits": 1, "files": 1}
                              for k, v in rates.items()},
                 "words": words, "documents": 1, "total_hits": len(rates)}

    def test_a_check_firing_far_more_on_the_measured_text_discriminates(self):
        rows = scan.compare_activity(self._corpus({"a": 3.0}),
                                      self._corpus({"a": 0.1}))
        self.assertEqual(rows["a"]["verdict"], "discriminates")

    def test_a_check_firing_equally_on_both_has_no_signal(self):
        rows = scan.compare_activity(self._corpus({"a": 2.84}),
                                      self._corpus({"a": 2.76}))
        self.assertEqual(rows["a"]["verdict"], "no signal")

    def test_a_check_firing_more_on_the_control_is_backwards(self):
        """identifier_in_prose scored 0.00 on generated text and 7.19 on
        human documentation. A check like that penalises the target."""
        rows = scan.compare_activity(self._corpus({"a": 0.0}),
                                      self._corpus({"a": 7.19}))
        self.assertEqual(rows["a"]["verdict"], "backwards")

    def test_a_check_firing_on_neither_is_silent_not_discriminating(self):
        """Zero against zero is no evidence at all. Calling it a
        discriminator would promote every dead check to a good one."""
        rows = scan.compare_activity(self._corpus({"a": 0.0}),
                                      self._corpus({"a": 0.0}))
        self.assertEqual(rows["a"]["verdict"], "silent")
        self.assertIsNone(rows["a"]["ratio"])

    def test_never_firing_on_the_control_does_not_divide_by_zero(self):
        rows = scan.compare_activity(self._corpus({"a": 3.08}),
                                      self._corpus({"a": 0.0}))
        self.assertEqual(rows["a"]["verdict"], "discriminates")
        self.assertIsNone(rows["a"]["ratio"])

    def test_a_check_absent_from_the_control_is_still_reported(self):
        rows = scan.compare_activity(self._corpus({"a": 1.0}),
                                      self._corpus({}))
        self.assertIn("a", rows)
        self.assertEqual(rows["a"]["control_per_1k"], 0.0)

    def test_the_real_ruleset_is_measurable_end_to_end(self):
        ruleset = rulesets.get_ruleset("slopwatch")
        directory = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, directory)
        with open(os.path.join(directory, "a.md"), "w") as f:
            f.write("**Bold** everywhere. **More** bold. **Still** bold.\n")
        report = scan.scan_tree([directory], REPO_ROOT, rulesets,
                                 ruleset_id="slopwatch")
        activity = scan.check_activity(report, ruleset)
        rows = scan.compare_activity(activity, activity)
        self.assertEqual(set(rows), set(ruleset.list_checks()))
        for row in rows.values():
            self.assertIn(row["verdict"], {"discriminates", "no signal",
                                            "backwards", "silent"})
