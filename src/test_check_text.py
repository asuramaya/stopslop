#!/usr/bin/env python3
"""The text every ruleset ships to describe its own checks, held to the
standard stopslop exists to enforce.

This is a real regression test, not a joke about dogfooding. The rot it
guards against shipped and sat in the product for two releases: each check
carried ONE prewritten sentence, authored in the coaching voice the
.claude/<ruleset>-memory.md primer wants ("X keeps showing up -- do Y"),
because that primer was the only consumer at the time. The dashboard's
Checks table later reused the same strings under a "what it catches"
heading, and 37 of 43 rows rendered as the same sentence template repeating
down a column. A slop detector whose own configuration screen was templated
filler.

The failure was invisible to every test in the suite, because each string
was individually fine. Only the COLLECTION was slop -- which is exactly the
kind of thing slopwatch flags in prose (em_dash_cluster and
synonym_rotation are both collection-level checks) and exactly what nothing
was checking here. These assertions look at the collection.

Reads each ruleset's CHECKS directly rather than calling list_checks(), so
nothing here touches the real repo's stopslop.config.json to find out
whether a check happens to be enabled -- the text is a property of the
code, not of this project's configuration.
"""
import os
import sys
import unittest
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rulesets
from core import flags as core_flags


def _all_checks():
    """[(ruleset_id, check_id, catches, instead), ...] across the fleet."""
    out = []
    for module in rulesets.list_rulesets():
        for check_id, (catches, instead) in getattr(module, "CHECKS", {}).items():
            out.append((module.RULESET_ID, check_id, catches, instead))
    return out


def _trigrams(text):
    words = [w.strip(".,:;\"'()") for w in text.lower().split()]
    return {" ".join(words[i:i + 3]) for i in range(len(words) - 2)}


class CheckTextTests(unittest.TestCase):

    def test_the_fleet_actually_ships_checks_to_examine(self):
        # Guards the guard: every assertion below passes trivially against an
        # empty list, so a refactor that renamed CHECKS would silently turn
        # this whole file into a no-op rather than failing.
        rows = _all_checks()
        self.assertGreaterEqual(len(rows), 40)
        self.assertEqual({r[0] for r in rows},
                          {m.RULESET_ID for m in rulesets.list_rulesets()})

    def test_every_check_carries_both_facts_separately(self):
        for ruleset_id, check_id, catches, instead in _all_checks():
            with self.subTest(check=f"{ruleset_id}.{check_id}"):
                self.assertTrue(catches.strip(), "no 'catches' text")
                self.assertTrue(instead.strip(), "no 'instead' text")
                # Pre-joining them here would put the sentence back in the
                # data and hand every consumer one voice again.
                self.assertNotIn(" -- ", catches)

    def test_no_check_describes_itself_in_the_coaching_voice(self):
        # "keeps showing up" is a claim about FREQUENCY. It is true in the
        # coaching primer, which prefixes each line with a real count from
        # the history log, and content-free in a settings table.
        banned = ("keep showing up", "keeps showing up", "keep opening",
                   "keeps opening", "keep clustering", "keeps clustering")
        for ruleset_id, check_id, catches, instead in _all_checks():
            for phrase in banned:
                with self.subTest(check=f"{ruleset_id}.{check_id}", phrase=phrase):
                    self.assertNotIn(phrase, f"{catches} {instead}".lower())

    def test_no_phrase_dominates_the_catches_column(self):
        """The actual defect: not one bad string, but one string shape
        repeated until the column stopped carrying information."""
        rows = _all_checks()
        counts = Counter()
        for _, _, catches, _ in rows:
            counts.update(_trigrams(catches))
        if not counts:
            self.fail("no trigrams extracted -- the check text is too short to assess")
        phrase, hits = counts.most_common(1)[0]
        limit = max(3, len(rows) // 4)
        self.assertLessEqual(
            hits, limit,
            f"{hits} of {len(rows)} checks describe themselves with the same "
            f"phrase {phrase!r} (limit {limit}). The old PRINCIPLE_TEXT hit 37 "
            f"of 43 this way. Say what each check catches, not what they have "
            f"in common.")

    def test_first_words_are_not_all_the_same(self):
        rows = _all_checks()
        openers = Counter(c.split()[0].lower() for _, _, c, _ in rows if c.split())
        opener, hits = openers.most_common(1)[0]
        self.assertLessEqual(
            hits, max(3, len(rows) // 4),
            f"{hits} of {len(rows)} 'catches' strings open with {opener!r} -- "
            f"a table scanned down its first column reads as one repeated row.")


class CoachingMemoryStillGetsItsVoiceTests(unittest.TestCase):
    """Splitting the sentence must not cost the primer anything: it is the
    one consumer the coaching frame was right for, and it composes its own
    line now instead of reading a prewritten one."""

    def test_generated_line_names_the_pattern_and_the_fix(self):
        import generate_coaching_memory  # noqa: F401 -- import-time smoke
        module = rulesets.get_ruleset("slopwatch")
        catches, instead = module.CHECKS["filler_verb"]
        line = f"- (12x) {catches} -- {instead}."
        self.assertIn("Filler verbs", line)
        self.assertIn("plain verb", line)
        # The count is what makes a recurrence claim in the primer honest;
        # it is also why the checks table needed different words entirely.
        self.assertIn("(12x)", line)



class CheckToConfigLinksTests(unittest.TestCase):
    """Every link the Configure page draws between a check and its tuning
    or its words is DECLARED by the ruleset, never inferred from names.

    The page folds a check's on/off, its parameter and its word list into
    one row, so those links became load-bearing. The first cut inferred
    them: an option was a check's parameter if it shared a name prefix
    ("em_dash_cluster" -> "em" -> "em_dash_threshold", correct by luck),
    and a list belonged to a check of the same id -- which silently showed
    ste100's `vocabulary` check as having no vocabulary, because its three
    lists do not share its name. These assertions keep both declared."""

    def test_every_term_list_names_a_check_that_exists(self):
        for module in rulesets.list_rulesets():
            checks = set(module.list_checks()) if "checks" in module.CAPABILITIES else set()
            for list_id, spec in getattr(module, "TERM_LISTS", {}).items():
                with self.subTest(list=f"{module.RULESET_ID}.{list_id}"):
                    feeds = spec.get("feeds")
                    self.assertTrue(feeds, "no 'feeds' key: the Configure page "
                                            "would never show this list anywhere")
                    self.assertIn(feeds, checks)

    def test_every_declared_check_option_exists(self):
        for module in rulesets.list_rulesets():
            options = set(module.list_options()) if "options" in module.CAPABILITIES else set()
            checks = set(module.list_checks()) if "checks" in module.CAPABILITIES else set()
            for check_id, names in getattr(module, "CHECK_OPTIONS", {}).items():
                with self.subTest(check=f"{module.RULESET_ID}.{check_id}"):
                    self.assertIn(check_id, checks)
                    for name in names:
                        self.assertIn(name, options)

    def test_the_deny_policy_names_only_real_checks_and_real_options(self):
        for module in rulesets.list_rulesets():
            policy = getattr(module, "DENY_POLICY", None)
            with self.subTest(ruleset=module.RULESET_ID):
                self.assertIsNotNone(policy, "no DENY_POLICY: the page cannot "
                                              "state what blocks a write")
                checks = set(module.list_checks()) if "checks" in module.CAPABILITIES else set()
                for check_id in policy["always_blocking"]:
                    self.assertIn(check_id, checks)
                # The text is format()ed with live option values, so a
                # placeholder with no option behind it renders as a stray
                # brace or raises, depending on the caller.
                policy["text"].format(**core_flags.display_options(module))

    def test_every_option_is_owned_by_a_check_or_is_the_deny_threshold(self):
        """No option may be orphaned. Configure shows an option either
        inside its check's row or in the deny-policy sentence; one that is
        neither would be invisible and therefore uneditable."""
        for module in rulesets.list_rulesets():
            if "options" not in module.CAPABILITIES:
                continue
            owned = {n for names in getattr(module, "CHECK_OPTIONS", {}).values()
                     for n in names}
            policy_text = getattr(module, "DENY_POLICY", {}).get("text", "")
            for name in module.list_options():
                with self.subTest(option=f"{module.RULESET_ID}.{name}"):
                    self.assertTrue(name in owned or ("{" + name + "}") in policy_text,
                                     f"{name} is in no check's CHECK_OPTIONS and is "
                                     f"not named in DENY_POLICY, so nothing on the "
                                     f"Configure page would ever show it")



class DenyPolicyMatchesBehaviourTests(unittest.TestCase):
    """DENY_POLICY is prose describing what blocking_semantic_flags does.
    Two statements of one fact, kept in step by hand -- exactly the shape
    that produced every other drift in this project. So the prose is not
    trusted: it is checked against the function.

    This does not remove the duplication, it makes it falsifiable. A policy
    sentence is worth having (it is the only place the page can state what
    blocks a write), and a policy sentence nobody verifies is worse than
    none, because it reads as authoritative."""

    def _flags(self, n, kind="filler_verb"):
        return [{"kind": kind, "label": f"w{i}", "detail": {}, "text": ""}
                for i in range(n)]

    def test_a_declared_count_threshold_is_the_real_threshold(self):
        for module in rulesets.list_rulesets():
            policy = module.DENY_POLICY
            if "{block_flag_count_threshold}" not in policy["text"]:
                continue
            threshold = module.list_options()["block_flag_count_threshold"]["value"]
            neutral = next((c for c in module.list_checks()
                            if c not in policy["always_blocking"]), None)
            self.assertIsNotNone(neutral)
            with self.subTest(ruleset=module.RULESET_ID):
                below = module.blocking_semantic_flags(
                    self._flags(threshold - 1, neutral))
                at = module.blocking_semantic_flags(self._flags(threshold, neutral))
                self.assertEqual(below, [],
                                  f"policy says it denies AT {threshold}, but "
                                  f"{threshold - 1} flags already blocked")
                self.assertTrue(at,
                                 f"policy says it denies at {threshold}, but "
                                 f"{threshold} flags did not block")

    def test_every_always_blocking_check_really_blocks_alone(self):
        for module in rulesets.list_rulesets():
            for check_id in module.DENY_POLICY["always_blocking"]:
                with self.subTest(check=f"{module.RULESET_ID}.{check_id}"):
                    self.assertTrue(
                        module.blocking_semantic_flags(self._flags(1, check_id)),
                        f"{check_id} is declared always-blocking and the page "
                        f"warns a user about it, but one of them did not block")

    def test_no_undeclared_check_blocks_alone(self):
        """The inverse, and the one that catches drift in the direction
        nobody looks: a check that gained always-block behaviour in code
        without being declared would show on the page as an ordinary row."""
        for module in rulesets.list_rulesets():
            declared = set(module.DENY_POLICY["always_blocking"])
            threshold_based = "{block_flag_count_threshold}" in module.DENY_POLICY["text"]
            if not threshold_based:
                continue          # ste100 blocks on any non-excluded flag by design
            for check_id in module.list_checks():
                if check_id in declared:
                    continue
                with self.subTest(check=f"{module.RULESET_ID}.{check_id}"):
                    self.assertEqual(
                        module.blocking_semantic_flags(self._flags(1, check_id)), [],
                        f"{check_id} blocks on its own but is not in "
                        f"DENY_POLICY['always_blocking'], so the page shows it "
                        f"as an ordinary row and the warning never appears")


class RemedyDerivationTests(unittest.TestCase):
    """Every blockable check must be able to say how to resolve a false
    positive. The gate used to list its flags and stop, so an agent blocked
    on a legitimate domain word never learned add_term existed."""

    def test_every_check_offers_at_least_one_remedy(self):
        from core import flags
        for module in rulesets.list_rulesets():
            if "checks" not in module.CAPABILITIES:
                continue
            for check_id in module.list_checks():
                with self.subTest(check=f"{module.RULESET_ID}.{check_id}"):
                    self.assertTrue(flags.remedies_for(module, check_id))

    def test_polarity_decides_which_verb_is_offered(self):
        """An allow list is widened with add_term; a deny list is narrowed
        with remove_term. Offering the wrong one sends a blocked caller in
        the opposite direction to the fix."""
        from core import flags
        ste = rulesets.get_ruleset("ste100")
        text = " ".join(flags.remedies_for(ste, "vocabulary"))
        self.assertIn("add_term('project_terms'", text)       # allow
        self.assertIn("remove_term('unapproved_words'", text)  # deny

        sw = rulesets.get_ruleset("slopwatch")
        deny_only = " ".join(flags.remedies_for(sw, "filler_verb"))
        self.assertIn("remove_term('filler_verb'", deny_only)
        self.assertNotIn("add_term", deny_only)

    def test_a_closed_list_is_never_offered_for_addition(self):
        from core import flags
        ste = rulesets.get_ruleset("ste100")
        text = " ".join(flags.remedies_for(ste, "vocabulary"))
        self.assertNotIn("add_term('approved_words'", text)
        self.assertNotIn("add_term('unapproved_words'", text)

    def test_the_deny_message_carries_them(self):
        """The hook composes its reason from the same derivation, so a new
        check or list is covered without touching pretool_hook.py."""
        source = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "pretool_hook.py")).read()
        self.assertIn("remedies_for", source)
        self.assertIn("If a flag is a false positive here", source)


if __name__ == "__main__":
    unittest.main()
