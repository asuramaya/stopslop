#!/usr/bin/env python3
"""Tests for core/config.py's path -> ruleset resolution, and for
rulesets/__init__.py's registration contract. Pure stdlib unittest, no
dependency on any real ruleset -- uses small fake modules so this suite
stays meaningful even while ste100/slopwatch are mid-migration.

Run with:
    cd src && python3 -m unittest core.test_config -v
or, once other ruleset suites exist:
    python3 -m unittest discover -s src -p 'test_*.py'
"""
import json
import os
import tempfile
import types
import unittest

from core import config
import rulesets


PROJECT_ROOT = "/fake/project/root"


def _fake_ruleset(ruleset_id, capabilities=frozenset()):
    """A minimal module-shaped object satisfying the required contract
    surface, for registry conformance tests -- never touches real linting
    logic, just needs the right attribute names to exist."""
    mod = types.SimpleNamespace()
    mod.__name__ = f"fake_{ruleset_id}"
    mod.RULESET_ID = ruleset_id
    mod.RULESET_NAME = ruleset_id.upper()
    mod.CAPABILITIES = capabilities
    mod.lint_and_gate = lambda text, context=None, file_path=None: {"mechanical": [], "semantic": []}
    mod.blocking_semantic_flags = lambda semantic_flags: []
    mod.apply_mechanical_fixes = lambda text, file_path=None: text
    if "terms" in capabilities:
        mod.list_term_lists = lambda file_path=None: {}
        mod.add_term = lambda list_id, term, note="", force=False: {}
        mod.remove_term = lambda list_id, term: {}
    if "word_lookup" in capabilities:
        mod.check_word = lambda word: {}
    if "checks" in capabilities:
        mod.list_checks = lambda: {}
        mod.set_enabled_checks = lambda check_ids: None
        mod.set_checks_enabled = lambda states: None
    if "options" in capabilities:
        mod.list_options = lambda: {}
        mod.set_options = lambda options: None
    return mod


class RegistryConformanceTests(unittest.TestCase):
    """Exercises the exact same conformance rules rulesets._register()
    enforces, against a private per-test registry dict (never the real,
    process-wide rulesets._REGISTRY) so these tests can't pollute each other
    or the real registry other test modules rely on. _register_into()
    mirrors rulesets._register()'s logic rather than calling it directly,
    since the real function always writes into module-level _REGISTRY."""

    def _register_into(self, reg, module):
        missing = [a for a in rulesets.REQUIRED_ATTRS if not hasattr(module, a)]
        if missing:
            raise rulesets.InvalidRulesetError(f"missing {missing}")
        for cap in module.CAPABILITIES:
            cap_missing = [a for a in rulesets.CAPABILITY_ATTRS.get(cap, ())
                            if not hasattr(module, a)]
            if cap_missing:
                raise rulesets.InvalidRulesetError(f"missing capability attrs {cap_missing}")
        if module.RULESET_ID in reg._REGISTRY:
            raise rulesets.InvalidRulesetError("duplicate id")
        reg._REGISTRY[module.RULESET_ID] = module

    def test_well_formed_ruleset_registers_cleanly(self):
        reg = types.SimpleNamespace(_REGISTRY={})
        self._register_into(reg, _fake_ruleset("demo"))
        self.assertIn("demo", reg._REGISTRY)

    def test_missing_required_attr_rejected(self):
        mod = _fake_ruleset("demo")
        del mod.blocking_semantic_flags
        reg = types.SimpleNamespace(_REGISTRY={})
        with self.assertRaises(rulesets.InvalidRulesetError):
            self._register_into(reg, mod)

    def test_declared_capability_without_backing_methods_rejected(self):
        mod = _fake_ruleset("demo", capabilities=frozenset({"terms"}))
        del mod.add_term
        reg = types.SimpleNamespace(_REGISTRY={})
        with self.assertRaises(rulesets.InvalidRulesetError):
            self._register_into(reg, mod)

    def test_empty_capabilities_is_valid(self):
        mod = _fake_ruleset("demo", capabilities=frozenset())
        reg = types.SimpleNamespace(_REGISTRY={})
        self._register_into(reg, mod)  # must not raise
        self.assertEqual(reg._REGISTRY["demo"].CAPABILITIES, frozenset())

    def test_duplicate_id_rejected(self):
        reg = types.SimpleNamespace(_REGISTRY={})
        self._register_into(reg, _fake_ruleset("demo"))
        with self.assertRaises(rulesets.InvalidRulesetError):
            self._register_into(reg, _fake_ruleset("demo"))

    def test_checks_capability_well_formed_registers_cleanly(self):
        # "checks"/"options" were informal hasattr() duck-typing until this
        # session's modularity pass -- this proves they're now real,
        # registry-enforced capabilities, not ad hoc methods a ruleset
        # happens to have.
        reg = types.SimpleNamespace(_REGISTRY={})
        self._register_into(reg, _fake_ruleset("demo", capabilities=frozenset({"checks"})))
        self.assertIn("demo", reg._REGISTRY)

    def test_checks_capability_without_set_enabled_checks_rejected(self):
        mod = _fake_ruleset("demo", capabilities=frozenset({"checks"}))
        del mod.set_enabled_checks
        reg = types.SimpleNamespace(_REGISTRY={})
        with self.assertRaises(rulesets.InvalidRulesetError):
            self._register_into(reg, mod)

    def test_checks_capability_without_the_merge_shape_rejected(self):
        # Declaring "checks" obligates BOTH write shapes. A ruleset offering
        # only the replace form invites the bug the dashboard shipped: a
        # partial list saved through a call that reads it as the total one.
        mod = _fake_ruleset("demo", capabilities=frozenset({"checks"}))
        del mod.set_checks_enabled
        reg = types.SimpleNamespace(_REGISTRY={})
        with self.assertRaises(rulesets.InvalidRulesetError):
            self._register_into(reg, mod)

    def test_terms_capability_without_remove_term_rejected(self):
        mod = _fake_ruleset("demo", capabilities=frozenset({"terms"}))
        del mod.remove_term
        reg = types.SimpleNamespace(_REGISTRY={})
        with self.assertRaises(rulesets.InvalidRulesetError):
            self._register_into(reg, mod)

    def test_no_ruleset_declares_a_retired_capability(self):
        # "glossary" and "wordlists" collapsed into one "terms" capability
        # (they were opposite polarities of one concept, not two concepts).
        # A ruleset still declaring either would register cleanly -- unknown
        # capability strings obligate nothing -- and then silently fail to
        # appear in the Vocabulary UI, which reads CAPABILITIES. Catch it
        # here instead.
        retired = {"glossary", "wordlists"}
        for mod in rulesets.list_rulesets():
            self.assertEqual(mod.CAPABILITIES & retired, frozenset(),
                             f"{mod.RULESET_ID} still declares a retired capability")

    def test_options_capability_well_formed_registers_cleanly(self):
        reg = types.SimpleNamespace(_REGISTRY={})
        self._register_into(reg, _fake_ruleset("demo", capabilities=frozenset({"options"})))
        self.assertIn("demo", reg._REGISTRY)

    def test_real_rulesets_declare_the_capabilities_they_implement(self):
        # Every real registered ruleset -- not a fake -- must already
        # satisfy its own declared capabilities, since _register() already
        # enforced this at import time; this just asserts the shape a
        # caller (dashboard.py, stopslop.py) actually relies on.
        for mod in rulesets.list_rulesets():
            for cap in mod.CAPABILITIES:
                for attr in rulesets.CAPABILITY_ATTRS.get(cap, ()):
                    self.assertTrue(hasattr(mod, attr),
                                     f"{mod.RULESET_ID} declares {cap!r} but has no {attr}")

    def test_real_registry_get_unknown_raises(self):
        with self.assertRaises(rulesets.UnknownRulesetError):
            rulesets.get_ruleset("__does_not_exist__")

    def test_real_registry_list_is_sorted_by_id(self):
        ids = [m.RULESET_ID for m in rulesets.list_rulesets()]
        self.assertEqual(ids, sorted(ids))


class LoadRulesTests(unittest.TestCase):
    def test_no_config_file_returns_defaults(self):
        rules = config.load_rules(PROJECT_ROOT, config_file="/nonexistent/stopslop.config.json")
        self.assertEqual(rules, config.DEFAULT_RULES)

    def test_config_file_overrides_defaults(self, ):
        import json
        import tempfile
        import os
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump({"rulesets": [{"glob": "*.md", "ruleset": "custom"}]}, f)
            path = f.name
        try:
            rules = config.load_rules(PROJECT_ROOT, config_file=path)
            self.assertEqual(rules, [{"glob": "*.md", "ruleset": "custom"}])
        finally:
            os.unlink(path)


class SaveRulesTests(unittest.TestCase):
    def _fake_registry(self, known_ids=("ste100",)):
        return types.SimpleNamespace(
            get_ruleset=lambda rid: rid if rid in known_ids else (_ for _ in ()).throw(
                rulesets.UnknownRulesetError(rid)),
        )

    def test_writes_valid_rules(self):
        import json
        import tempfile
        import os
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            rules = [{"glob": "*.md", "ruleset": "ste100"}, {"glob": ".claude/*", "ruleset": None}]
            config.save_rules(tmp, rules, self._fake_registry(), config_file=path)
            with open(path) as f:
                written = json.load(f)
            self.assertEqual(written["rulesets"], rules)

    def test_unknown_ruleset_id_raises_before_writing(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            rules = [{"glob": "*.md", "ruleset": "typo-name"}]
            with self.assertRaises(rulesets.UnknownRulesetError):
                config.save_rules(tmp, rules, self._fake_registry(), config_file=path)
            self.assertFalse(os.path.exists(path))

    def test_preserves_glossary_packs_key_already_in_the_file(self):
        # Regression guard: save_rules used to blindly overwrite the whole
        # file, which would have silently dropped "glossary_packs" the
        # moment both config concerns lived in the same file.
        import json
        import tempfile
        import os
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            with open(path, "w") as f:
                json.dump({"glossary_packs": {"ste100": ["microsoft-style-guide"]}}, f)
            config.save_rules(tmp, [{"glob": "*.md", "ruleset": "ste100"}],
                               self._fake_registry(), config_file=path)
            with open(path) as f:
                written = json.load(f)
            self.assertEqual(written["glossary_packs"], {"ste100": ["microsoft-style-guide"]})

    def test_malformed_rule_raises(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            with self.assertRaises(ValueError):
                config.save_rules(tmp, [{"glob": "*.md"}], self._fake_registry(), config_file=path)
            self.assertFalse(os.path.exists(path))

    def test_round_trips_through_load_rules(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            rules = [{"glob": "*.py", "ruleset": "ste100"}]
            config.save_rules(tmp, rules, self._fake_registry(), config_file=path)
            self.assertEqual(config.load_rules(tmp, config_file=path), rules)


class PathScopedPacksConfigTests(unittest.TestCase):
    """Packs hang off the routing RULE that matches a path, and the rule
    also names which term list each pack feeds. The old shape
    ("glossary_packs": {"ste100": [...]}) threw the path away; the shape
    after that put a `target` inside the pack, which made the pack author
    responsible for knowing its consumer."""

    def _write(self, tmp, rules):
        path = os.path.join(tmp, "stopslop.config.json")
        with open(path, "w") as f:
            json.dump({"rulesets": rules}, f)
        return path

    def test_no_config_file_returns_no_packs(self):
        self.assertEqual(
            config.packs_for_path(PROJECT_ROOT, os.path.join(PROJECT_ROOT, "a.md"),
                                   list_id="project_terms",
                                   config_file="/nonexistent/stopslop.config.json"),
            [])

    def test_first_matching_rule_wins(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, [
                {"glob": "docs/security/*.md", "ruleset": "ste100",
                 "packs": {"project_terms": ["nist-security"]}},
                {"glob": "*.md", "ruleset": "ste100",
                 "packs": {"project_terms": ["mdn-glossary"]}},
            ])
            self.assertEqual(
                config.packs_for_path(tmp, os.path.join(tmp, "docs/security/threat.md"),
                                       list_id="project_terms", config_file=path),
                ["nist-security"])

    def test_different_paths_same_ruleset_get_different_packs(self):
        # The whole point of the reshape: docs/security/ and blog/ both
        # route to ste100 but must not share a glossary.
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, [
                {"glob": "docs/security/*.md", "ruleset": "ste100",
                 "packs": {"project_terms": ["nist-security"]}},
                {"glob": "blog/*.md", "ruleset": "ste100"},
            ])
            self.assertEqual(
                config.packs_for_path(tmp, os.path.join(tmp, "docs/security/x.md"),
                                       list_id="project_terms", config_file=path),
                ["nist-security"])
            self.assertEqual(
                config.packs_for_path(tmp, os.path.join(tmp, "blog/x.md"),
                                       list_id="project_terms", config_file=path),
                [])

    def test_packs_are_scoped_to_the_list_they_were_bound_to(self):
        # One rule, two lists, different packs. Impossible while a pack
        # named its own single target list.
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, [
                {"glob": "*.md", "ruleset": "ste100",
                 "packs": {"project_terms": ["nist-security"],
                            "other_list": ["mdn-glossary"]}},
            ])
            target = os.path.join(tmp, "a.md")
            self.assertEqual(
                config.packs_for_path(tmp, target, list_id="project_terms",
                                       config_file=path), ["nist-security"])
            self.assertEqual(
                config.packs_for_path(tmp, target, list_id="other_list",
                                       config_file=path), ["mdn-glossary"])
            self.assertEqual(
                config.packs_for_path(tmp, target, list_id="unbound_list",
                                       config_file=path), [])

    def test_one_pack_can_feed_two_lists_at_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, [
                {"glob": "*.md", "ruleset": "ste100",
                 "packs": {"a": ["mdn-glossary"], "b": ["mdn-glossary"]}},
            ])
            target = os.path.join(tmp, "a.md")
            for list_id in ("a", "b"):
                self.assertEqual(
                    config.packs_for_path(tmp, target, list_id=list_id,
                                           config_file=path), ["mdn-glossary"])

    def test_no_list_id_returns_every_pack_the_rule_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, [
                {"glob": "*.md", "ruleset": "ste100",
                 "packs": {"a": ["mdn-glossary"], "b": ["nist-security"]}},
            ])
            self.assertEqual(
                sorted(config.packs_for_path(tmp, os.path.join(tmp, "a.md"),
                                              config_file=path)),
                ["mdn-glossary", "nist-security"])

    def test_rule_without_packs_key_yields_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, [{"glob": "*.md", "ruleset": "ste100"}])
            self.assertEqual(
                config.packs_for_path(tmp, os.path.join(tmp, "a.md"),
                                       list_id="project_terms", config_file=path), [])

    def test_free_text_resolves_via_the_synthetic_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, [{"glob": "*.md", "ruleset": "ste100",
                                       "packs": {"project_terms": ["mdn-glossary"]}}])
            self.assertEqual(
                config.packs_for_path(tmp, None, list_id="project_terms",
                                       config_file=path),
                ["mdn-glossary"])

    def test_set_rule_packs_round_trips(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, [{"glob": "*.md", "ruleset": "ste100"}])
            config.set_rule_packs(tmp, "*.md", "project_terms", ["nist-security"],
                                   config_file=path)
            self.assertEqual(
                config.packs_for_path(tmp, os.path.join(tmp, "a.md"),
                                       list_id="project_terms", config_file=path),
                ["nist-security"])

    def test_set_rule_packs_leaves_other_lists_alone(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, [{"glob": "*.md", "ruleset": "ste100",
                                       "packs": {"keep": ["mdn-glossary"]}}])
            config.set_rule_packs(tmp, "*.md", "project_terms", ["nist-security"],
                                   config_file=path)
            self.assertEqual(
                config.packs_for_path(tmp, os.path.join(tmp, "a.md"),
                                       list_id="keep", config_file=path),
                ["mdn-glossary"])

    def test_set_rule_packs_empty_detaches_only_that_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, [{"glob": "*.md", "ruleset": "ste100",
                                       "packs": {"project_terms": ["nist-security"],
                                                  "keep": ["mdn-glossary"]}}])
            config.set_rule_packs(tmp, "*.md", "project_terms", [], config_file=path)
            with open(path) as f:
                written = json.load(f)
            self.assertEqual(written["rulesets"][0]["packs"], {"keep": ["mdn-glossary"]})

    def test_set_rule_packs_empty_removes_the_key_when_nothing_is_left(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, [{"glob": "*.md", "ruleset": "ste100",
                                       "packs": {"project_terms": ["nist-security"]}}])
            config.set_rule_packs(tmp, "*.md", "project_terms", [], config_file=path)
            with open(path) as f:
                written = json.load(f)
            self.assertNotIn("packs", written["rulesets"][0])

    def test_set_rule_packs_rejects_an_unknown_pack_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, [{"glob": "*.md", "ruleset": "ste100"}])
            with self.assertRaises(ValueError):
                config.set_rule_packs(tmp, "*.md", "project_terms", ["nist-securty"],
                                       known_packs={"nist-security"}, config_file=path)

    def test_set_rule_packs_rejects_an_unknown_glob(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, [{"glob": "*.md", "ruleset": "ste100"}])
            with self.assertRaises(ValueError):
                config.set_rule_packs(tmp, "*.rst", "project_terms", ["nist-security"],
                                       config_file=path)

    def test_save_rules_preserves_packs_a_routing_edit_did_not_mention(self):
        # The routing editor and the Vocabulary tab are separate widgets;
        # one must not silently wipe the other's work.
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, [{"glob": "*.md", "ruleset": "ste100",
                                       "packs": {"project_terms": ["nist-security"]}}])
            config.save_rules(tmp, [{"glob": "*.md", "ruleset": "ste100"}],
                               rulesets, config_file=path)
            self.assertEqual(
                config.packs_for_path(tmp, os.path.join(tmp, "a.md"),
                                       list_id="project_terms", config_file=path),
                ["nist-security"])

    def test_malformed_packs_value_contributes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, [{"glob": "*.md", "ruleset": "ste100",
                                       "packs": "not-a-dict"}])
            self.assertEqual(
                config.packs_for_path(tmp, os.path.join(tmp, "a.md"),
                                       list_id="project_terms", config_file=path), [])


class DisabledChecksConfigTests(unittest.TestCase):
    def test_no_config_file_returns_empty(self):
        # Opposite default from glossary packs: an empty list here means
        # "nothing disabled, every check runs" -- an unconfigured clone
        # must see the exact same checks as before this feature existed.
        self.assertEqual(
            config.disabled_checks(PROJECT_ROOT, "slopwatch",
                                    config_file="/nonexistent/stopslop.config.json"),
            [])

    def test_round_trips_through_save_and_load(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            config.save_disabled_checks(tmp, "slopwatch", ["stock_adverb", "colon_reveal"],
                                         config_file=path)
            self.assertEqual(
                config.disabled_checks(tmp, "slopwatch", config_file=path),
                ["stock_adverb", "colon_reveal"])

    def test_ruleset_not_mentioned_returns_empty(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            config.save_disabled_checks(tmp, "slopwatch", ["stock_adverb"], config_file=path)
            self.assertEqual(
                config.disabled_checks(tmp, "codewatch", config_file=path), [])

    def test_preserves_glossary_packs_key_already_in_the_file(self):
        import json
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            with open(path, "w") as f:
                json.dump({"glossary_packs": {"ste100": ["nist-security"]}}, f)
            config.save_disabled_checks(tmp, "slopwatch", ["stock_adverb"], config_file=path)
            with open(path) as f:
                written = json.load(f)
            self.assertEqual(written["glossary_packs"], {"ste100": ["nist-security"]})


class RulesetOptionsConfigTests(unittest.TestCase):
    def test_no_config_file_returns_empty_dict(self):
        self.assertEqual(
            config.ruleset_options(PROJECT_ROOT, "slopwatch",
                                    config_file="/nonexistent/stopslop.config.json"),
            {})

    def test_round_trips_through_save_and_load(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            config.save_ruleset_options(tmp, "slopwatch", {"em_dash_threshold": 5}, config_file=path)
            self.assertEqual(
                config.ruleset_options(tmp, "slopwatch", config_file=path),
                {"em_dash_threshold": 5})

    def test_ruleset_not_mentioned_returns_empty_dict(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            config.save_ruleset_options(tmp, "slopwatch", {"em_dash_threshold": 5}, config_file=path)
            self.assertEqual(config.ruleset_options(tmp, "codewatch", config_file=path), {})

    def test_preserves_rulesets_key_already_in_the_file(self):
        import json
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            with open(path, "w") as f:
                json.dump({"rulesets": [{"glob": "*.md", "ruleset": "ste100"}]}, f)
            config.save_ruleset_options(tmp, "slopwatch", {"em_dash_threshold": 5}, config_file=path)
            with open(path) as f:
                written = json.load(f)
            self.assertEqual(written["rulesets"], [{"glob": "*.md", "ruleset": "ste100"}])


class ResolveRulesetIdDefaultRulesTests(unittest.TestCase):
    """resolve_ruleset_id() against DEFAULT_RULES (no config file) --
    codewatch (*.py) and slopwatch (the repo-root README.md) are now real,
    deliberate defaults (see DEFAULT_RULES's own docstring for why), not
    just the original ste100-only truth table; this suite pins the current
    intentional shape so a *future* change is still a deliberate, reviewed
    edit here rather than silent drift."""

    CASES = [
        (PROJECT_ROOT + "/README.md", "slopwatch"),      # repo-root README only
        (PROJECT_ROOT + "/docs/README.md", "ste100"),     # a nested README isn't "the" README
        (PROJECT_ROOT + "/notes.txt", "ste100"),
        (PROJECT_ROOT + "/notes.rst", "ste100"),
        (PROJECT_ROOT + "/docs/sub/dir/file.md", "ste100"),
        (PROJECT_ROOT + "/script.py", "codewatch"),
        (PROJECT_ROOT + "/src/pkg/module.py", "codewatch"),
        (PROJECT_ROOT + "/data.json", None),
        (PROJECT_ROOT + "/README.MD", None),          # case-sensitive, matches old .endswith()
        (PROJECT_ROOT + "/.claude/settings.local.json", None),
        (PROJECT_ROOT + "/.claude/notes.md", None),     # under .claude/ even though .md
        (PROJECT_ROOT + "/.claude/sub/deep.md", None),
        (PROJECT_ROOT + "/.claude/script.py", None),      # .claude/ wins over *.py too
        ("/some/other/repo/outside.md", None),           # outside project root entirely
    ]

    def test_default_rules_truth_table(self):
        for file_path, expected in self.CASES:
            with self.subTest(file_path=file_path):
                self.assertEqual(
                    config.resolve_ruleset_id(file_path, PROJECT_ROOT), expected)

    def test_no_config_file_never_resolves_to_an_undeclared_id(self):
        # Guards against the registry growing a THIRD ruleset silently
        # changing what an unconfigured clone lints against -- only ids
        # DEFAULT_RULES itself deliberately names are reachable here.
        default_ids = {r["ruleset"] for r in config.DEFAULT_RULES}
        for file_path, _ in self.CASES:
            resolved = config.resolve_ruleset_id(file_path, PROJECT_ROOT)
            self.assertIn(resolved, default_ids)


class ResolveRulesetTests(unittest.TestCase):
    def test_resolves_to_registered_module(self):
        registry = types.SimpleNamespace(
            get_ruleset=lambda rid: _fake_ruleset(rid) if rid == "ste100" else (_ for _ in ()).throw(
                rulesets.UnknownRulesetError(rid)),
            UnknownRulesetError=rulesets.UnknownRulesetError,
        )
        # Not README.md -- that's the repo-root slopwatch default now; this
        # test only cares about generic *.md -> ste100 resolution.
        mod = config.resolve_ruleset(PROJECT_ROOT + "/notes.md", PROJECT_ROOT, registry)
        self.assertEqual(mod.RULESET_ID, "ste100")

    def test_out_of_scope_path_returns_none_without_touching_registry(self):
        registry = types.SimpleNamespace(
            get_ruleset=lambda rid: (_ for _ in ()).throw(AssertionError("should not be called")),
        )
        # Not script.py -- that's a real codewatch default now; this test
        # needs a path genuinely out of scope under every default rule.
        result = config.resolve_ruleset(PROJECT_ROOT + "/data.json", PROJECT_ROOT, registry)
        self.assertIsNone(result)

    def test_unregistered_ruleset_id_raises_loudly(self):
        import json
        import tempfile
        import os
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump({"rulesets": [{"glob": "*.md", "ruleset": "typo-name"}]}, f)
            path = f.name
        try:
            with self.assertRaises(rulesets.UnknownRulesetError):
                config.resolve_ruleset(PROJECT_ROOT + "/README.md", PROJECT_ROOT,
                                        rulesets, config_file=path)
        finally:
            os.unlink(path)


class MatchingRuleTests(unittest.TestCase):
    """The one rule that decides a path -- the shared answer to
    first-match-wins that resolve_ruleset_id and packs_for_path both go
    through now, and that the dashboard used to approximate with a loop of
    its own asking a subtly different question."""

    RULES = [
        {"glob": ".claude/*", "ruleset": None},
        {"glob": "README.md", "ruleset": "slopwatch"},
        {"glob": "*.md", "ruleset": "ste100",
         "packs": {"project_terms": ["mdn-glossary"]}},
    ]

    def setUp(self):
        tmp = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        json.dump({"rulesets": self.RULES}, tmp)
        tmp.close()
        self.cfg = tmp.name

    def tearDown(self):
        os.unlink(self.cfg)

    def _rule(self, rel):
        return config.matching_rule(os.path.join(PROJECT_ROOT, rel),
                                     PROJECT_ROOT, config_file=self.cfg)

    def test_returns_the_first_matching_rule_whole(self):
        rule = self._rule("guide.md")
        self.assertEqual(rule["glob"], "*.md")
        self.assertEqual(rule["packs"], {"project_terms": ["mdn-glossary"]})

    def test_an_earlier_rule_wins_even_though_a_later_one_also_matches(self):
        # The bug this function exists to prevent. README.md matches BOTH
        # the slopwatch rule and the ste100 `*.md` rule. Asking "the first
        # rule matching this path AND ste100" -- which is what the
        # dashboard's own loop asked when hanging a pack somewhere --
        # answers `*.md`, a rule the gate never reaches for this file, so
        # the pack binding it wrote could never fire.
        self.assertEqual(self._rule("README.md")["glob"], "README.md")
        self.assertEqual(self._rule("README.md")["ruleset"], "slopwatch")

    def test_an_explicitly_unscoped_path_returns_its_rule_not_none(self):
        # "no rule matched" and "a rule deliberately put this out of scope"
        # are different facts; resolve_ruleset_id flattens both to None, so
        # a caller that needs to tell them apart (the dashboard says which
        # of the two it is) asks here instead.
        rule = self._rule(".claude/settings.json")
        self.assertIsNotNone(rule)
        self.assertIsNone(rule["ruleset"])
        self.assertIsNone(self._rule("notes.org"))

    def test_resolve_ruleset_id_agrees_with_it_on_every_path(self):
        for rel in ("guide.md", "README.md", ".claude/settings.json", "notes.org"):
            with self.subTest(path=rel):
                rule = self._rule(rel)
                self.assertEqual(
                    config.resolve_ruleset_id(os.path.join(PROJECT_ROOT, rel),
                                               PROJECT_ROOT, config_file=self.cfg),
                    rule["ruleset"] if rule else None)

    def test_a_path_outside_the_project_matches_nothing(self):
        self.assertIsNone(config.matching_rule("/elsewhere/guide.md",
                                                PROJECT_ROOT, config_file=self.cfg))


class MergeDisabledChecksTests(unittest.TestCase):
    """Merge semantics for checks, the counterpart to save_disabled_checks's
    replace. The dashboard's Checks table saved a FILTERED view through the
    replace call, so typing "filler" in its search box and pressing Save
    disabled every check the search had hidden -- 18 of slopwatch's 20."""

    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.cfg = os.path.join(self._dir.name, "stopslop.config.json")

    def tearDown(self):
        self._dir.cleanup()

    def _disabled(self):
        return config.disabled_checks(self._dir.name, "slopwatch", config_file=self.cfg)

    def test_naming_two_checks_leaves_every_other_alone(self):
        config.save_disabled_checks(self._dir.name, "slopwatch",
                                     ["emoji_in_prose"], config_file=self.cfg)
        config.merge_disabled_checks(self._dir.name, "slopwatch",
                                      {"filler_verb": False, "filler_opener": True},
                                      config_file=self.cfg)
        # emoji_in_prose was never named, so it stays exactly as it was --
        # this is the whole point, and the assertion that fails under the
        # replace-shaped call the dashboard was using.
        self.assertEqual(self._disabled(), ["emoji_in_prose", "filler_verb"])

    def test_re_enabling_lifts_a_disable(self):
        config.save_disabled_checks(self._dir.name, "slopwatch",
                                     ["filler_verb"], config_file=self.cfg)
        config.merge_disabled_checks(self._dir.name, "slopwatch",
                                      {"filler_verb": True}, config_file=self.cfg)
        self.assertEqual(self._disabled(), [])

    def test_it_does_not_disturb_another_ruleset(self):
        config.save_disabled_checks(self._dir.name, "ste100", ["modal"],
                                     config_file=self.cfg)
        config.merge_disabled_checks(self._dir.name, "slopwatch",
                                      {"filler_verb": False}, config_file=self.cfg)
        self.assertEqual(config.disabled_checks(self._dir.name, "ste100",
                                                 config_file=self.cfg), ["modal"])

    def test_the_replace_shape_still_replaces(self):
        # Both shapes stay available and mean different things: the CLI's
        # `checks --enable a b c` means "these and only these" and depends
        # on replace. Merge is not a fix applied to replace, it is the
        # other legitimate half.
        config.save_disabled_checks(self._dir.name, "slopwatch",
                                     ["filler_verb"], config_file=self.cfg)
        config.save_disabled_checks(self._dir.name, "slopwatch",
                                     ["emoji_in_prose"], config_file=self.cfg)
        self.assertEqual(self._disabled(), ["emoji_in_prose"])


class KnownExtensionsTests(unittest.TestCase):
    def test_default_extensions(self):
        self.assertEqual(config.known_extensions(PROJECT_ROOT,
                          config_file="/nonexistent/stopslop.config.json"),
                          {".md", ".txt", ".rst", ".py"})


if __name__ == "__main__":
    unittest.main()
