#!/usr/bin/env python3
"""docs/adding-a-ruleset.md must describe the contract that exists.

That document is the only artifact a fourth-ruleset author reads, and every
way it can be wrong is silent: follow a stale contract and your ruleset
registers, runs, and renders with no deny policy, no tuning links and no
words -- with nothing anywhere saying why.

It has gone stale twice in this project's short life. First when `terms`
replaced the `glossary` and `wordlist` capabilities and the doc kept
documenting register_term/unregister_term/list_terms. Then again within the
same day: the doc was rewritten for the real contract, and DENY_POLICY,
CHECK_OPTIONS and the term-list `feeds` field were added over the next two
commits without it being touched.

Twice is a pattern, and "remember to update the docs" is the mitigation
that already failed twice. So the names are checked. This does not verify
that the PROSE is correct -- nothing can -- but a name the contract
requires and the doc never mentions is a fact, and facts can be asserted.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rulesets

DOC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "docs", "adding-a-ruleset.md")

# Names a ruleset may define that are not part of REQUIRED_ATTRS or any
# capability, but that the Configure page and the coaching primer read. A
# ruleset omitting one still registers, so nothing else catches their
# absence from the doc.
OPTIONAL_CONTRACT_NAMES = (
    "TRACKED_FILES", "CHECKS", "DENY_POLICY", "CHECK_OPTIONS",
    "TERM_LISTS", "stats",
)

# Per-term-list keys the resolver and the UI both honour.
TERM_LIST_KEYS = ("polarity", "feeds", "content_kind", "accepts_packs",
                   "accepts_additions", "built_ins")


class ContractDocTests(unittest.TestCase):

    def setUp(self):
        with open(DOC) as f:
            self.text = f.read()

    def test_the_doc_exists_and_is_substantial(self):
        # Guards the guard: every assertion below passes against an empty
        # file only if it is never read, so fail loudly on a stub.
        self.assertGreater(len(self.text), 2000)

    def test_every_required_attribute_is_documented(self):
        for name in rulesets.REQUIRED_ATTRS:
            with self.subTest(name=name):
                self.assertTrue(
                    name in self.text,
                    f"{name} is required of every ruleset and the contract "
                    f"doc never mentions it")

    def test_every_capability_and_its_methods_are_documented(self):
        for capability, attrs in rulesets.CAPABILITY_ATTRS.items():
            with self.subTest(capability=capability):
                self.assertIn(f'"{capability}"', self.text)
            for name in attrs:
                with self.subTest(capability=capability, name=name):
                    self.assertTrue(
                        name in self.text,
                        f"declaring {capability!r} obligates {name}, "
                        f"which the contract doc never mentions")

    def test_every_optional_contract_name_a_ruleset_ships_is_documented(self):
        for name in OPTIONAL_CONTRACT_NAMES:
            shipped = [m.RULESET_ID for m in rulesets.list_rulesets()
                       if hasattr(m, name)]
            if not shipped:
                continue        # nothing ships it: nothing to document yet
            with self.subTest(name=name, shipped_by=shipped):
                self.assertTrue(
                    name in self.text,
                    f"{shipped} define {name} and the doc never mentions it, "
                    f"so a fourth ruleset omits it and fails silently")

    def test_every_term_list_key_in_use_is_documented(self):
        in_use = set()
        for module in rulesets.list_rulesets():
            for spec in getattr(module, "TERM_LISTS", {}).values():
                in_use |= set(spec)
        for key in sorted(in_use & set(TERM_LIST_KEYS)):
            with self.subTest(key=key):
                self.assertTrue(
                    key in self.text,
                    f"term lists declare {key!r} and the doc never mentions it")

    def test_the_doc_names_no_capability_that_no_longer_exists(self):
        """The other direction, and the one that actually bit: the doc kept
        describing `glossary` and `wordlists` for a while after `terms`
        replaced both."""
        for dead in ('"glossary"', '"wordlists"', '"options"', "PRINCIPLE_TEXT",
                      "add_wordlist_term", "list_wordlists", "DENY_POLICY",
                      "CHECK_OPTIONS", "list_options", "set_options"):
            with self.subTest(dead=dead):
                # A HISTORICAL mention is fine and useful; a mention in the
                # contract sections is not. The capabilities section is where
                # an author looks for what to implement.
                section = self.text.split("## Capabilities", 1)[-1]
                section = section.split("## How to register it", 1)[0]
                self.assertNotIn(f"declare {dead}", section)
                self.assertNotIn(f"define {dead}", section)


if __name__ == "__main__":
    unittest.main()
