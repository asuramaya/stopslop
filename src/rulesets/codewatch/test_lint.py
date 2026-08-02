#!/usr/bin/env python3
"""Automated tests for rulesets/codewatch/lint.py -- same stdlib-unittest
structure as rulesets/slopwatch/test_lint.py, one TestCase per check plus
blocking-policy and integration tests.

Run with:
    cd src && python3 -m unittest rulesets.codewatch.test_lint -v
"""
import unittest

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
    def test_print_call_flags(self):
        hits = lint.check_print_debug("print('debug', value)")
        self.assertEqual(len(hits), 1)

    def test_ordinary_line_not_flagged(self):
        self.assertEqual(lint.check_print_debug("logger.info('started')"), [])


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

    def test_four_or_more_flags_block(self):
        code = (
            "# Return the processed result\n"
            "def f(items=[]):\n"
            "    print('debug')\n"
            "    if True:\n"
            "        pass\n"
        )
        r = lint.lint_and_gate(code)
        self.assertGreaterEqual(len(r["semantic_flags"]), 4)
        self.assertEqual(lint.blocking_semantic_flags(r["semantic_flags"]), r["semantic_flags"])


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


if __name__ == "__main__":
    unittest.main()
