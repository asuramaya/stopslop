#!/usr/bin/env python3
"""Automated regression tests for rulesets/ste100/lint.py, the actual rule
engine (formerly prototype/test_ste100_lint.py against
prototype/ste100_lint.py). Pure stdlib unittest -- no new dependency, so the
gate itself stays testable without the MCP venv (mcp_server.py is the only
thing in this repo that needs one).

Runs against the REAL loaded dictionary (dictionary.json), not a mock --
deliberately. Every regression test below encodes a bug that was only found
by testing against real data; a mocked dictionary would have hidden every
one of them the same way the old ~120-word stand-in did. Project-term-
dependent tests save and restore lint.PROJECT_TERMS so they don't depend on
this project's own glossary staying a specific shape.

Run with:
    cd src && python3 -m unittest rulesets.ste100.test_lint -v
or, to run every ruleset's suite together:
    cd src && python3 -m unittest discover -s . -p 'test_*.py'
"""
import os
import tempfile
import unittest

from core import terms as core_terms
from rulesets.ste100 import lint
from rulesets import ste100


class VocabularyTests(unittest.TestCase):
    def test_approved_word_passes_silently(self):
        self.assertEqual(lint.check_vocabulary("check"), [])

    def test_unapproved_word_with_replacement_flags(self):
        violations = lint.check_vocabulary("utilize")
        self.assertEqual(len(violations), 1)
        v = violations[0]
        self.assertEqual(v["type"], "unapproved_synonym")
        self.assertEqual(v["replacement"], "use")
        # Auto-fix is disabled for ALL vocabulary, unconditionally -- see
        # test_regression_pos_mismatch_not_autofixed for why.
        self.assertFalse(v["auto_fix"])

    def test_word_with_no_replacement_flags_distinctly(self):
        violations = lint.check_vocabulary("product")
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0]["type"], "unapproved_no_replacement")
        self.assertIsNone(violations[0]["replacement"])

    def test_unknown_word_flags_as_unknown_vocabulary(self):
        violations = lint.check_vocabulary("kubernetes")
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0]["type"], "unknown_vocabulary")

    def test_project_term_passes_silently(self):
        original = dict(lint.PROJECT_TERMS)
        try:
            lint.PROJECT_TERMS["kubernetes"] = {"note": "test"}
            self.assertEqual(lint.check_vocabulary("kubernetes"), [])
        finally:
            lint.PROJECT_TERMS.clear()
            lint.PROJECT_TERMS.update(original)

    def test_modal_words_never_appear_as_vocabulary_flags(self):
        # Regression: should/would/may/could/might used to fall through to
        # unknown_vocabulary and double-report alongside check_modals' own
        # kind:modal flag for the same word.
        for modal in ("should", "would", "may", "could", "might"):
            with self.subTest(modal=modal):
                self.assertEqual(lint.check_vocabulary(modal), [])


class BaseFormResolutionTests(unittest.TestCase):
    """The real dictionary lists headwords in base form only; these test
    that inflected forms (conjugations, plurals) still resolve correctly."""

    def test_conjugated_approved_verb_passes_silently(self):
        self.assertEqual(lint.check_vocabulary("checks"), [])
        self.assertEqual(lint.check_vocabulary("checked"), [])

    def test_irregular_be_forms_pass_silently(self):
        for form in ("is", "are", "was", "were", "been"):
            with self.subTest(form=form):
                self.assertEqual(lint.check_vocabulary(form), [])

    def test_conjugated_unapproved_verb_flags_but_does_not_autofix(self):
        violations = lint.check_vocabulary("utilizes")
        self.assertEqual(len(violations), 1)
        v = violations[0]
        self.assertEqual(v["type"], "unapproved_synonym")
        self.assertFalse(v["auto_fix"])
        self.assertIn("note", v)

    def test_approved_unapproved_pos_overlap_approved_wins(self):
        # "complete" is approved as a verb, unapproved as an adjective.
        # check_vocabulary is word-level, not POS-aware -- approved wins.
        self.assertEqual(lint.check_vocabulary("complete"), [])


class VocabAutoFixTests(unittest.TestCase):
    """fix_sentence must never rewrite vocabulary -- all auto-fix for
    UNAPPROVED_MAP is disabled. See the module-level comment above
    UNAPPROVED_NO_AUTOFIX in ste100_lint.py for the incident this responds
    to."""

    def test_regression_pos_mismatch_not_autofixed(self):
        # "real (adj)" maps to the single alternative "AGREE (v)" -- not a
        # synonym, the verb of a differently-structured sentence. Live
        # regression: this silently corrupted the project's own README.
        s = "The gauge shows the real quantity of fuel."
        self.assertEqual(lint.fix_sentence(s), s)

    def test_regression_ambiguous_replacement_not_autofixed(self):
        # "guide (v)" -> PUT, MOVE. Live regression: "the maintenance
        # guide" auto-"fixed" to "the maintenance put".
        s = "Refer to the maintenance guide."
        self.assertEqual(lint.fix_sentence(s), s)

    def test_regression_approved_word_precedence_in_fixer(self):
        # _vocab_sub used to have no APPROVED_WORDS check at all, unlike
        # check_vocabulary. Live regression: "could complete the task"
        # auto-"fixed" to "can full the task" (complete->FULL is the
        # UNAPPROVED adjective sense; the sentence uses the APPROVED verb
        # sense).
        s = "The operator could complete the task."
        fixed = lint.fix_sentence(s)
        self.assertIn("complete", fixed)
        self.assertNotIn("full", fixed)

    def test_simple_single_alternative_word_also_not_autofixed(self):
        # Confirms auto-fix is off UNCONDITIONALLY, not just for the risky
        # cases -- utilize->use is safe (verb-for-verb) but still doesn't
        # auto-fix, on purpose, since nothing currently distinguishes safe
        # single-alternative entries from unsafe ones like real->agree.
        s = "The system will utilize the cache."
        self.assertEqual(lint.fix_sentence(s), s)


class ModalTests(unittest.TestCase):
    def test_should_always_flags_never_autofixes(self):
        hits = lint.check_modals("He should not touch the panel.")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["rule"], "10.6")
        self.assertFalse(hits[0]["auto_fix"])

    def test_default_case_autofixes_to_table_default(self):
        hits = lint.check_modals("The operator could complete the task.")
        self.assertEqual(len(hits), 1)
        self.assertTrue(hits[0]["auto_fix"])
        self.assertEqual(hits[0]["replacement"], "can")

    def test_if_clause_heuristic(self):
        hits = lint.check_modals("If the pressure exceeds limits, the operator may stop the test.")
        may_hits = [h for h in hits if h["modal"] == "may"]
        self.assertEqual(len(may_hits), 1)
        self.assertEqual(may_hits[0]["replacement"], "can")

    def test_warning_heuristic(self):
        hits = lint.check_modals("WARNING: the operator might touch the hot surface.")
        might_hits = [h for h in hits if h["modal"] == "might"]
        self.assertEqual(len(might_hits), 1)
        self.assertEqual(might_hits[0]["replacement"], "must")

    def test_semi_modal_collocation_not_autofixed(self):
        hits = lint.check_modals("The operator may need to stop the test.")
        may_hits = [h for h in hits if h["modal"] == "may"]
        self.assertEqual(len(may_hits), 1)
        self.assertFalse(may_hits[0]["auto_fix"])
        self.assertEqual(may_hits[0]["rule"], "5.3/13.3")

    def test_regression_modal_vocab_collision(self):
        # check_vocabulary used to blindly substitute "may"->"can" with no
        # awareness of the collocation exception check_modals already
        # flags as non-auto-fixable. Live regression: "the operator may
        # need to stop the test" auto-"fixed" to "the operator can need to
        # stop the test".
        s = "The operator may need to stop the test."
        fixed = lint.fix_sentence(s)
        self.assertIn("may", fixed)
        self.assertNotIn(" can need", fixed)

    def test_modal_fix_matches_detection(self):
        # would/may/might/could resolve through the SAME function
        # (_modal_resolution) for both detection and fixing -- this checks
        # they can't independently disagree the way they used to.
        s = "The operator would complete the task."
        fixed = lint.fix_sentence(s)
        self.assertIn("will", fixed)


class IngFormTests(unittest.TestCase):
    def test_whitelisted_ing_noun_passes(self):
        self.assertEqual(lint.check_ing("Check the lighting circuit."), [])

    def test_non_whitelisted_ing_flags(self):
        hits = lint.check_ing("The system is monitoring the sensor.")
        self.assertTrue(any(h["word"] == "monitoring" for h in hits))

    def test_regression_ordinary_nouns_not_flagged(self):
        # Live regression: check_ing only exempted words in the real
        # dictionary or the ~9-word spec whitelist -- ordinary English
        # nouns the aviation dictionary never had reason to list (not
        # verb-derived at all) fell through and blocked the write.
        # "The meeting starts in the morning. Check the wing and the
        # ceiling before flight." denied over morning/wing/ceiling.
        hits = lint.check_ing("The meeting starts in the morning. "
                               "Check the wing and the ceiling before flight.")
        flagged = {h["word"].lower() for h in hits}
        self.assertNotIn("morning", flagged)
        self.assertNotIn("wing", flagged)
        self.assertNotIn("ceiling", flagged)

    def test_regression_software_domain_gerund_still_flags(self):
        # The fix above must not silently exempt real verb-derived misuse
        # just because the aviation-scoped dictionary doesn't list the
        # underlying verb -- "configure" has no dictionary entry at all,
        # unlike "monitor".
        hits = lint.check_ing("The system is configuring the network.")
        self.assertTrue(any(h["word"] == "configuring" for h in hits))


class LengthContextTests(unittest.TestCase):
    TWENTY_ONE_WORDS = ("Run the register command with the exact flagged word "
                         "and a short note that explains the reason for the new entry.")

    def test_description_context_uses_25_word_limit(self):
        self.assertIsNone(lint.check_length(self.TWENTY_ONE_WORDS, context="description"))

    def test_procedure_context_uses_20_word_limit(self):
        self.assertIsNotNone(lint.check_length(self.TWENTY_ONE_WORDS, context="procedure"))

    def test_numbered_list_item_forced_to_procedure_context(self):
        doc = "1. " + self.TWENTY_ONE_WORDS
        r = lint.lint_and_gate(doc, context="description")
        length_flags = [f for f in r["semantic_flags"] if f["kind"] == "length"]
        self.assertEqual(len(length_flags), 1)

    def test_bulleted_list_item_keeps_callers_context(self):
        doc = "- " + self.TWENTY_ONE_WORDS
        r = lint.lint_and_gate(doc, context="description")
        length_flags = [f for f in r["semantic_flags"] if f["kind"] == "length"]
        self.assertEqual(len(length_flags), 0)


class PunctuationTests(unittest.TestCase):
    def test_semicolon_flags_and_autofixes(self):
        hits = lint.check_punctuation("The system failed; the operator restarted it.")
        self.assertTrue(any(h["type"] == "semicolon" for h in hits))

    def test_known_contraction_flags_and_autofixes(self):
        hits = lint.check_punctuation("The system doesn't work.")
        self.assertTrue(any(h["type"] == "contraction" and h["replacement"] == "does not" for h in hits))

    def test_possessive_not_flagged(self):
        hits = lint.check_punctuation("Check the system's pressure.")
        self.assertEqual(hits, [])


class BlockingFlagsTests(unittest.TestCase):
    """The single source of truth for what the live gate actually acts
    on -- see pretool_hook.py and stopslop.py, both of which call this
    same function rather than keeping their own copy."""

    def test_unknown_vocabulary_excluded(self):
        r = lint.lint_and_gate("kubernetes", context="description")
        blocking = lint.blocking_semantic_flags(r["semantic_flags"])
        self.assertEqual(blocking, [])

    def test_unapproved_no_replacement_excluded(self):
        r = lint.lint_and_gate("The product is ready.", context="description")
        blocking = lint.blocking_semantic_flags(r["semantic_flags"])
        self.assertFalse(any(f["kind"] == "vocabulary" for f in blocking))

    def test_modal_should_still_blocks(self):
        r = lint.lint_and_gate("He should not touch the panel.", context="description")
        blocking = lint.blocking_semantic_flags(r["semantic_flags"])
        self.assertTrue(any(f["kind"] == "modal" for f in blocking))

    def test_passive_still_blocks(self):
        r = lint.lint_and_gate("The valve was opened.", context="description")
        blocking = lint.blocking_semantic_flags(r["semantic_flags"])
        self.assertTrue(any(f["kind"] == "passive" for f in blocking))


class LintAndGateIntegrationTests(unittest.TestCase):
    def test_clean_text_status_clean(self):
        r = lint.lint_and_gate("Do this work in a clean area.", context="description")
        self.assertEqual(r["status"], "clean")

    def test_mechanical_only_status(self):
        # Every word here is either approved or a base-form match, so the
        # only violation is the semicolon -- unlike "failed"/"restarted" in
        # an earlier draft of this test, which turned out to also carry
        # ordinary (denial-excluded) vocabulary flags that made status
        # "semantic_flags" even though the write would still pass the live
        # gate cleanly. See the comment on lint_and_gate's "status" field.
        r = lint.lint_and_gate("The system does not work; it does not start.", context="description")
        self.assertEqual(r["status"], "mechanical_violations")

    def test_semantic_flags_status(self):
        r = lint.lint_and_gate("He should not touch the panel.", context="description")
        self.assertEqual(r["status"], "semantic_flags")

    def test_code_fence_not_linted(self):
        doc = "Do this work.\n\n```\nyou should not retry forever and ever and ever\n```\n"
        r = lint.lint_and_gate(doc, context="description")
        self.assertEqual(r["status"], "clean")

    def test_inline_code_span_not_linted(self):
        doc = "See the note that says `you should not retry`."
        r = lint.lint_and_gate(doc, context="description")
        modal_flags = [f for f in r["semantic_flags"] if f["kind"] == "modal"]
        self.assertEqual(modal_flags, [])


class CheckToggleTests(unittest.TestCase):
    """list_checks()/set_enabled_checks() on the ste100 contract surface --
    same isolation technique as test_glossary_packs.py's own
    PackEnableDisableTests, so this never touches the real repo's own
    stopslop.config.json. ste100 previously had NO per-check toggles at
    all (only slopwatch/codewatch did) -- this is the parity fix."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        open(os.path.join(self._tmp.name, "stopslop.py"), "w").close()
        self._orig_find_root = ste100.paths.find_project_root
        ste100.paths.find_project_root = lambda _file: self._tmp.name

    def tearDown(self):
        ste100.paths.find_project_root = self._orig_find_root
        self._tmp.cleanup()

    def test_every_check_enabled_by_default(self):
        checks = ste100.list_checks()
        self.assertEqual(set(checks), lint.ALL_CHECK_IDS)
        self.assertTrue(all(c["enabled"] for c in checks.values()))
        self.assertTrue(all(c["catches"] and c["instead"] for c in checks.values()))

    def test_disabling_modal_check_removes_its_flags_from_lint_and_gate(self):
        text = "He should not touch the panel."
        self.assertTrue(any(f["kind"] == "modal"
                             for f in lint.lint_and_gate(text)["semantic_flags"]))
        ste100.set_enabled_checks(lint.ALL_CHECK_IDS - {"modal"})
        self.assertFalse(any(f["kind"] == "modal"
                              for f in lint.lint_and_gate(text)["semantic_flags"]))

    def test_disabling_vocabulary_check_removes_its_flags(self):
        text = "The team will leverage the new process."
        self.assertTrue(any(f["kind"] == "vocabulary"
                             for f in lint.lint_and_gate(text)["mechanical_violations"]
                             + lint.lint_and_gate(text)["semantic_flags"]))
        ste100.set_enabled_checks(lint.ALL_CHECK_IDS - {"vocabulary"})
        r = lint.lint_and_gate(text)
        self.assertFalse(any(f["kind"] == "vocabulary"
                              for f in r["mechanical_violations"] + r["semantic_flags"]))

    def test_unknown_check_id_raises_and_does_not_write(self):
        with self.assertRaises(ValueError):
            ste100.set_enabled_checks(["__not_a_real_check__"])
        self.assertFalse(os.path.exists(os.path.join(self._tmp.name, "stopslop.config.json")))


class DictionaryAsTermListsTests(unittest.TestCase):
    """The real ASD-STE100 dictionary is now two term lists rather than two
    module globals nothing else could see.

    Before this it was the only vocabulary in the project outside the
    term-list model: 1,990 words that could not be listed, searched or
    curated, while every other ruleset's built-ins could. A project cannot
    edit a git-tracked standard, so disagreeing with a handful of entries
    meant forking it -- suppression is what makes the control real."""

    def setUp(self):
        self._orig = lint._paths.find_project_root
        self._tmp = tempfile.TemporaryDirectory()
        open(os.path.join(self._tmp.name, "stopslop.py"), "w").close()
        lint._paths.find_project_root = lambda _f: self._tmp.name
        core_terms._migration_checked.clear()

    def tearDown(self):
        lint._paths.find_project_root = self._orig
        core_terms._migration_checked.clear()
        self._tmp.cleanup()

    def _suppress(self, list_id, word):
        core_terms.remove_term("ste100", lint.TERM_LISTS, self._tmp.name,
                                list_id, word)
        return lint.suppressed_vocabulary()

    def test_both_dictionary_halves_are_declared_as_lists(self):
        self.assertEqual(len(lint.TERM_LISTS["approved_words"]["built_ins"]),
                          len(lint.APPROVED_WORDS))
        self.assertEqual(lint.TERM_LISTS["approved_words"]["polarity"], "allow")
        self.assertEqual(lint.TERM_LISTS["unapproved_words"]["polarity"], "deny")

    def test_forbidden_words_carry_their_replacement_as_metadata(self):
        built = lint.TERM_LISTS["unapproved_words"]["built_ins"]
        word = next(w for w, r in lint.UNAPPROVED_MAP.items() if r)
        self.assertIn(lint.UNAPPROVED_MAP[word], built[word]["note"])

    def test_no_suppression_by_default(self):
        self.assertEqual(lint.suppressed_vocabulary(), lint._NO_SUPPRESSION)

    def test_suppressing_a_forbidden_word_stops_it_being_flagged(self):
        word = next(w for w, r in lint.UNAPPROVED_MAP.items() if r)
        self.assertTrue(lint.check_vocabulary(word))
        sup = self._suppress("unapproved_words", word)
        self.assertEqual(lint.check_vocabulary(word, None, sup), [])

    def test_suppressing_an_approved_word_starts_flagging_it(self):
        word = "check"
        self.assertEqual(lint.check_vocabulary(word), [])
        sup = self._suppress("approved_words", word)
        self.assertTrue(lint.check_vocabulary(word, None, sup))

    def test_suppression_reaches_lint_and_gate(self):
        word = next(w for w, r in lint.UNAPPROVED_MAP.items() if r)
        text = f"You must {word} the panel."
        # Assert on the WORD, not on the "vocabulary" kind: other words in
        # the sentence ("panel") are legitimately unknown vocabulary and
        # produce their own flag of the same kind, so a kind-level
        # assertion would pass or fail for the wrong reason.
        flagged = lambda: [f.get("label") for f in
                            lint.lint_and_gate(text)["semantic_flags"]]
        self.assertIn(word, flagged())
        self._suppress("unapproved_words", word)
        self.assertNotIn(word, flagged())

    def test_a_suppressed_word_can_be_restored(self):
        word = next(w for w, r in lint.UNAPPROVED_MAP.items() if r)
        self._suppress("unapproved_words", word)
        core_terms.add_term("ste100", lint.TERM_LISTS, self._tmp.name,
                             "unapproved_words", word)
        self.assertEqual(lint.suppressed_vocabulary(), lint._NO_SUPPRESSION)
        self.assertTrue(lint.check_vocabulary(word))

    def test_dictionary_words_appear_in_the_flat_term_index(self):
        import rulesets
        rows = core_terms.term_index(rulesets, self._tmp.name)
        by_list = {}
        for row in rows:
            by_list[row["list"]] = by_list.get(row["list"], 0) + 1
        self.assertEqual(by_list["approved_words"], len(lint.APPROVED_WORDS))
        self.assertGreater(by_list["unapproved_words"], 1000)

    def test_an_unresolvable_project_root_never_breaks_the_gate(self):
        lint._paths.find_project_root = lambda _f: (_ for _ in ()).throw(OSError("x"))
        self.assertEqual(lint.suppressed_vocabulary(), lint._NO_SUPPRESSION)


if __name__ == "__main__":
    unittest.main()
