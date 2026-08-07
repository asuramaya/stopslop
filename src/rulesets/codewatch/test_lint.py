#!/usr/bin/env python3
"""Automated tests for rulesets/codewatch/lint.py -- same stdlib-unittest
structure as rulesets/slopwatch/test_lint.py, one TestCase per check plus
blocking-policy and integration tests.

Run with:
    cd src && python3 -m unittest rulesets.codewatch.test_lint -v
"""
import os
import tempfile
import unittest

from core import terms as _terms
from rulesets import codewatch
from rulesets.codewatch import lint


class TrivialCommentTests(unittest.TestCase):
    def test_verb_stem_comment_flags(self):
        hits = lint.check_trivial_comment("# Return the processed result", None)
        self.assertEqual(len(hits), 1)

    def test_explanatory_comment_not_flagged(self):
        self.assertEqual(
            lint.check_trivial_comment("# Return early because the cache is warm", None), [])

    def test_long_comment_not_flagged(self):
        long_comment = "# " + ("x" * 70)
        self.assertEqual(lint.check_trivial_comment(long_comment, None), [])

    def test_commented_out_code_not_flagged(self):
        self.assertEqual(lint.check_trivial_comment("# result = fetch(items);", None), [])

    def test_ordinary_code_line_not_flagged(self):
        self.assertEqual(lint.check_trivial_comment("result = fetch(items)", None), [])

    def test_section_divider_followed_by_blank_line_not_flagged(self):
        self.assertEqual(lint.check_trivial_comment("# Setup", ""), [])


class NarrativeCommentTests(unittest.TestCase):
    def test_decorative_separator_flags(self):
        hits = lint.check_narrative_comment("# ==========================")
        self.assertEqual(len(hits), 1)

    def test_section_header_flags(self):
        hits = lint.check_narrative_comment("# Phase 1: setup")
        self.assertEqual(len(hits), 1)

    def test_cross_reference_flags(self):
        hits = lint.check_narrative_comment("# see below for the real implementation")
        self.assertEqual(len(hits), 1)

    def test_justification_opener_flags(self):
        hits = lint.check_narrative_comment("# This function handles retry logic")
        self.assertEqual(len(hits), 1)

    def test_ordinary_comment_not_flagged(self):
        self.assertEqual(lint.check_narrative_comment("# cache TTL in seconds"), [])


class MetaCommentTests(unittest.TestCase):
    def test_plan_reference_flags(self):
        hits = lint.check_meta_comment("# as per the requirements this must retry twice")
        self.assertEqual(len(hits), 1)

    def test_before_after_narration_flags(self):
        hits = lint.check_meta_comment("# previously this used a different cache key")
        self.assertEqual(len(hits), 1)

    def test_genuine_why_context_not_flagged(self):
        # Contains "because" -- real WHY context is exempt even if it also
        # narrates a before/after change, matching scanaislop's own design.
        self.assertEqual(
            lint.check_meta_comment("# we used to call fetch directly, because the old API required it"),
            [])

    def test_ordinary_comment_not_flagged(self):
        self.assertEqual(lint.check_meta_comment("# cache TTL in seconds"), [])


class SwallowedExceptionTests(unittest.TestCase):
    def test_bare_except_pass_flags(self):
        lines = ["try:", "    do_thing()", "except Exception:", "    pass"]
        hits = lint.check_swallowed_exception(lines, 2)
        self.assertEqual(len(hits), 1)

    def test_intentionally_named_ignore_not_flagged(self):
        lines = ["try:", "    do_thing()", "except Exception as _:", "    pass"]
        self.assertEqual(lint.check_swallowed_exception(lines, 2), [])

    def test_except_with_real_handling_not_flagged(self):
        lines = ["try:", "    do_thing()", "except Exception:", "    log.warning('failed')"]
        self.assertEqual(lint.check_swallowed_exception(lines, 2), [])

    def test_non_except_line_not_flagged(self):
        self.assertEqual(lint.check_swallowed_exception(["x = 1"], 0), [])


class MutableDefaultArgTests(unittest.TestCase):
    def test_list_default_flags(self):
        hits = lint.check_mutable_default_arg("def f(items=[]):")
        self.assertEqual(len(hits), 1)

    def test_dict_default_flags(self):
        hits = lint.check_mutable_default_arg("def f(cache={}):")
        self.assertEqual(len(hits), 1)

    def test_none_default_not_flagged(self):
        self.assertEqual(lint.check_mutable_default_arg("def f(items=None):"), [])

    def test_non_def_line_not_flagged(self):
        self.assertEqual(lint.check_mutable_default_arg("items = []"), [])


class PrintDebugTests(unittest.TestCase):
    def test_print_call_in_a_library_module_flags(self):
        hits = lint.check_print_debug("print('debug', value)", is_script=False)
        self.assertEqual(len(hits), 1)

    def test_ordinary_line_not_flagged(self):
        self.assertEqual(lint.check_print_debug("logger.info('started')", is_script=False), [])

    def test_print_call_in_a_script_shaped_file_not_flagged(self):
        # Live regression: build_glossary_pack_mdn.py's own print()s inside
        # def main() -- called only from `if __name__ == "__main__":` --
        # were being denied by the live gate for being "leftover debug
        # output" when they were the script's entire purpose. Found by
        # actually scanning this project's own real files (stopslop.py
        # scan), not a synthetic fixture.
        self.assertEqual(lint.check_print_debug("print('Wrote output.json')", is_script=True), [])


class IsScriptTests(unittest.TestCase):
    def test_file_with_main_guard_is_a_script(self):
        lines = ["def main():", "    pass", "", 'if __name__ == "__main__":', "    main()"]
        self.assertTrue(lint._is_script(lines))

    def test_single_quoted_main_guard_also_counts(self):
        self.assertTrue(lint._is_script(["if __name__ == '__main__':", "    main()"]))

    def test_plain_library_module_is_not_a_script(self):
        lines = ["def helper():", "    return 1"]
        self.assertFalse(lint._is_script(lines))

    def test_bare_launcher_with_no_def_or_class_is_a_script(self):
        # Live regression: mcp_launch.py is pure top-level code (an
        # os.execv() launcher, no functions at all) -- it has no __main__
        # guard because it doesn't need one, but its print() is exactly as
        # intentional as a guarded script's. Found via stopslop.py scan
        # against this project's own real mcp_launch.py.
        lines = ["import sys", "", "if not ok:", "    print('no venv', file=sys.stderr)",
                  "    sys.exit(1)"]
        self.assertTrue(lint._is_script(lines))

    def test_module_with_any_function_is_not_a_bare_launcher(self):
        lines = ["def helper():", "    return 1", "", "print('debug')"]
        self.assertFalse(lint._is_script(lines))


class TodoStubTests(unittest.TestCase):
    def test_untracked_todo_flags(self):
        hits = lint.check_todo_stub("# TODO fix this someday")
        self.assertEqual(len(hits), 1)

    def test_todo_with_issue_number_not_flagged(self):
        self.assertEqual(lint.check_todo_stub("# TODO(#123): fix this"), [])

    def test_todo_with_tracker_key_not_flagged(self):
        self.assertEqual(lint.check_todo_stub("# FIXME PROJ-456"), [])

    def test_no_todo_marker_not_flagged(self):
        self.assertEqual(lint.check_todo_stub("# cache TTL in seconds"), [])


class GenericNamingTests(unittest.TestCase):
    def test_numbered_helper_flags(self):
        hits = lint.check_generic_naming("helper_1 = compute()")
        self.assertEqual(len(hits), 1)

    def test_numbered_data_flags(self):
        hits = lint.check_generic_naming("def process(data2):")
        self.assertEqual(len(hits), 1)

    def test_descriptive_name_not_flagged(self):
        self.assertEqual(lint.check_generic_naming("retry_count = 3"), [])

    def test_extra_stem_not_flagged_without_registration(self):
        self.assertEqual(lint.check_generic_naming("widget1 = compute()"), [])

    def test_extra_stem_flags_when_passed(self):
        hits = lint.check_generic_naming("widget1 = compute()", extra=["widget"])
        self.assertEqual(len(hits), 1)

    def test_built_in_stem_still_flags_with_extra_present(self):
        hits = lint.check_generic_naming("helper_1 = compute()", extra=["widget"])
        self.assertEqual(len(hits), 1)


class TautologicalAssertTests(unittest.TestCase):
    def test_assert_true_flags(self):
        self.assertEqual(len(lint.check_tautological_assert("assert True")), 1)

    def test_real_assertion_not_flagged(self):
        self.assertEqual(lint.check_tautological_assert("assert result == expected"), [])


class ConstantConditionTests(unittest.TestCase):
    def test_if_true_flags(self):
        hits = lint.check_constant_condition("if True:")
        self.assertEqual(len(hits), 1)

    def test_while_false_flags(self):
        hits = lint.check_constant_condition("while False:")
        self.assertEqual(len(hits), 1)

    def test_real_condition_not_flagged(self):
        self.assertEqual(lint.check_constant_condition("if ready:"), [])


class BlockingFlagsTests(unittest.TestCase):
    """codewatch's blocking policy is a third distinct shape from ste100's
    exclusion list and slopwatch's pure count threshold: swallowed_exception
    always blocks, everything else needs density."""

    def test_single_flag_does_not_block(self):
        r = lint.lint_and_gate("# Return the processed result\nresult = fetch()\n")
        self.assertEqual(lint.blocking_semantic_flags(r["semantic_flags"]), [])

    def test_swallowed_exception_alone_blocks(self):
        code = "try:\n    do_thing()\nexcept Exception:\n    pass\n"
        r = lint.lint_and_gate(code)
        blocking = lint.blocking_semantic_flags(r["semantic_flags"])
        self.assertTrue(any(f["kind"] == "swallowed_exception" for f in blocking))

    def test_many_different_warn_checks_together_still_do_not_block(self):
        # The old shared aggregate ("N flags total, from ANY checks,
        # denies") is retired -- each check's own {threshold, action}
        # decides now, independently. See slopwatch's identical test and
        # CheckToggleAndOptionsTests below for turning a specific check
        # to "block" instead.
        code = (
            "# Return the processed result\n"
            "def f(items=[]):\n"
            "    print('debug')\n"
            "    if True:\n"
            "        pass\n"
        )
        r = lint.lint_and_gate(code)
        self.assertGreaterEqual(len(r["semantic_flags"]), 4)
        self.assertEqual(lint.blocking_semantic_flags(r["semantic_flags"]), [])


class LintAndGateIntegrationTests(unittest.TestCase):
    def test_clean_code_status_clean(self):
        r = lint.lint_and_gate("def add(a, b):\n    return a + b\n")
        self.assertEqual(r["status"], "clean")

    def test_semantic_flags_status(self):
        r = lint.lint_and_gate("# Return the processed result\nresult = fetch()\n")
        self.assertEqual(r["status"], "semantic_flags")

    def test_no_mechanical_violations_ever(self):
        # codewatch has no auto-fixable checks -- every flag needs a
        # judgment call.
        code = "print('debug')\nassert True\n"
        r = lint.lint_and_gate(code)
        self.assertEqual(r["mechanical_violations"], [])

    def test_apply_mechanical_fixes_is_a_no_op(self):
        code = "print('debug')\n"
        self.assertEqual(lint.apply_mechanical_fixes(code), code)

    def test_print_debug_exempt_in_a_script_shaped_file_end_to_end(self):
        code = (
            "def main():\n"
            "    print('Wrote output.json')\n"
            "    print('done')\n"
            "\n"
            'if __name__ == "__main__":\n'
            "    main()\n"
        )
        r = lint.lint_and_gate(code)
        kinds = [f["kind"] for f in r["semantic_flags"]]
        self.assertNotIn("print_debug", kinds)

    def test_print_debug_still_flagged_with_no_main_guard(self):
        code = "def main():\n    print('Wrote output.json')\n"
        r = lint.lint_and_gate(code)
        kinds = [f["kind"] for f in r["semantic_flags"]]
        self.assertIn("print_debug", kinds)


class CheckToggleAndOptionsTests(unittest.TestCase):
    """Same isolation technique as slopwatch's own CheckToggleAndOptionsTests
    and ste100's PackEnableDisableTests -- a temp project root so this
    never touches the real repo's own stopslop.config.json."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        open(os.path.join(self._tmp.name, "stopslop.py"), "w").close()
        self._orig_find_root = lint._paths.find_project_root
        lint._paths.find_project_root = lambda _file: self._tmp.name

    def tearDown(self):
        lint._paths.find_project_root = self._orig_find_root
        self._tmp.cleanup()

    def test_every_check_enabled_by_default(self):
        checks = codewatch.list_checks()
        self.assertEqual(set(checks), lint.ALL_CHECK_IDS)
        self.assertTrue(all(c["enabled"] for c in checks.values()))

    def test_disabling_a_check_removes_its_flags_from_lint_and_gate(self):
        # Wrapped in a real function (not a bare "print('debug')" one-liner)
        # so this stays a genuine print_debug hit under _is_script's
        # no-def-or-class-anywhere exemption -- this test is only checking
        # the enable/disable toggle machinery, not print_debug's own rules.
        code = "def helper():\n    print('debug')\n"
        self.assertTrue(any(f["kind"] == "print_debug"
                             for f in lint.lint_and_gate(code)["semantic_flags"]))
        codewatch.set_enabled_checks(lint.ALL_CHECK_IDS - {"print_debug"})
        self.assertFalse(any(f["kind"] == "print_debug"
                              for f in lint.lint_and_gate(code)["semantic_flags"]))

    def test_disabling_swallowed_exception_check_lets_it_stop_always_blocking(self):
        # swallowed_exception "always blocks" only applies to flags that
        # actually reach blocking_semantic_flags -- disabling the check
        # removes it from semantic_flags entirely, upstream of that policy.
        code = "except ValueError:\n    pass\n"
        r = lint.lint_and_gate(code)
        self.assertTrue(lint.blocking_semantic_flags(r["semantic_flags"]))
        codewatch.set_enabled_checks(lint.ALL_CHECK_IDS - {"swallowed_exception"})
        r2 = lint.lint_and_gate(code)
        self.assertEqual(lint.blocking_semantic_flags(r2["semantic_flags"]), [])

    def test_unknown_check_id_raises_and_does_not_write(self):
        with self.assertRaises(ValueError):
            codewatch.set_enabled_checks(["__not_a_real_check__"])
        self.assertFalse(os.path.exists(os.path.join(self._tmp.name, "stopslop.config.json")))

    def test_default_check_config_before_any_override(self):
        cfg = codewatch.list_check_config()
        self.assertEqual(cfg["swallowed_exception"],
                          {"threshold": 1, "action": "block",
                           "default_threshold": 1, "default_action": "block"})
        self.assertEqual(cfg["generic_naming"],
                          {"threshold": 1, "action": "warn",
                           "default_threshold": 1, "default_action": "warn"})

    def test_action_override_changes_blocking_semantic_flags(self):
        flags = [{"kind": "generic_naming", "label": f"w{i}", "detail": {}, "text": ""}
                  for i in range(3)]
        self.assertEqual(lint.blocking_semantic_flags(flags), [])  # default action=warn
        codewatch.set_check_config("generic_naming", threshold=3, action="block")
        self.assertEqual(len(lint.blocking_semantic_flags(flags)), 3)

    def test_unknown_check_id_in_set_check_config_raises_and_does_not_write(self):
        with self.assertRaises(ValueError):
            codewatch.set_check_config("__not_a_real_check__", threshold=1)
        self.assertFalse(os.path.exists(os.path.join(self._tmp.name, "stopslop.config.json")))

    def test_invalid_threshold_raises(self):
        with self.assertRaises(ValueError):
            codewatch.set_check_config("generic_naming", threshold=0)
        with self.assertRaises(ValueError):
            codewatch.set_check_config("generic_naming", threshold="ten")

    def test_invalid_action_raises(self):
        with self.assertRaises(ValueError):
            codewatch.set_check_config("generic_naming", action="deny")


class TermListExtensibilityEndToEndTests(unittest.TestCase):
    """Same temp-project-root isolation as CheckToggleAndOptionsTests --
    proves a real add_term() call actually changes lint_and_gate's
    real-world behavior, not just the direct check_generic_naming() calls
    in GenericNamingTests above."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        open(os.path.join(self._tmp.name, "stopslop.py"), "w").close()
        self._orig_find_root = lint._paths.find_project_root
        lint._paths.find_project_root = lambda _file: self._tmp.name
        _terms._migration_checked.clear()

    def tearDown(self):
        lint._paths.find_project_root = self._orig_find_root
        self._tmp.cleanup()

    def test_registered_stem_reaches_lint_and_gate(self):
        code = "widget1 = compute()\n"
        self.assertNotIn("generic_naming",
                          [f["kind"] for f in lint.lint_and_gate(code)["semantic_flags"]])
        codewatch.add_term("generic_naming", "widget", "seen live in a real diff")
        self.assertIn("generic_naming",
                       [f["kind"] for f in lint.lint_and_gate(code)["semantic_flags"]])

    def test_removed_term_stops_flagging(self):
        codewatch.add_term("generic_naming", "widget")
        code = "widget1 = compute()\n"
        self.assertIn("generic_naming",
                       [f["kind"] for f in lint.lint_and_gate(code)["semantic_flags"]])
        codewatch.remove_term("generic_naming", "widget")
        self.assertNotIn("generic_naming",
                          [f["kind"] for f in lint.lint_and_gate(code)["semantic_flags"]])

    def test_list_term_lists_surfaces_project_terms(self):
        codewatch.add_term("generic_naming", "widget", "seen live in a real diff")
        lists = codewatch.list_term_lists()
        self.assertEqual(lists["generic_naming"]["project_terms"],
                          {"widget": {"note": "seen live in a real diff"}})

    def test_reports_deny_polarity_and_built_in_count(self):
        view = codewatch.list_term_lists()["generic_naming"]
        self.assertEqual(view["polarity"], "deny")
        self.assertEqual(view["built_in_count"], len(lint.GENERIC_NAME_STEMS))

    def test_unknown_list_id_raises_and_does_not_write(self):
        with self.assertRaises(_terms.UnknownTermListError):
            codewatch.add_term("__not_real__", "x")
        self.assertFalse(os.path.exists(os.path.join(self._tmp.name, "stopslop.config.json")))

    def test_removing_a_never_registered_term_is_a_no_op(self):
        codewatch.remove_term("generic_naming", "never-added")  # must not raise


if __name__ == "__main__":
    unittest.main()
