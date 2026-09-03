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
import importlib
import json
import os
import pkgutil
import sys
import tempfile
import textwrap
import types
import unittest

from core import config
import rulesets


def _register_into(reg, module):
    """Standalone copy of RegistryConformanceTests._register_into's logic,
    for DynamicDiscoveryTests below (which needs it outside a TestCase
    instance) -- mirrors rulesets._register() without ever writing into
    the real, process-wide rulesets._REGISTRY."""
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


PROJECT_ROOT = "/fake/project/root"


def _fake_ruleset(ruleset_id, capabilities=frozenset(), check_ids=(), term_lists=None):
    """A minimal module-shaped object satisfying the required contract
    surface, for registry conformance tests -- never touches real linting
    logic, just needs the right attribute names to exist. `check_ids` and
    `term_lists` let a caller give this fake real-looking checks/lists
    (default empty, the original behavior) for tests that need
    save_rules/orphaned_rule_extras to see something concrete to
    validate against."""
    mod = types.SimpleNamespace()
    mod.__name__ = f"fake_{ruleset_id}"
    mod.RULESET_ID = ruleset_id
    mod.RULESET_NAME = ruleset_id.upper()
    mod.CAPABILITIES = capabilities
    mod.lint_and_gate = lambda text, context=None, file_path=None: {"mechanical": [], "semantic": []}
    mod.blocking_semantic_flags = lambda semantic_flags: []
    mod.apply_mechanical_fixes = lambda text, file_path=None: text
    if term_lists is not None:
        mod.TERM_LISTS = term_lists
    if "terms" in capabilities:
        mod.list_term_lists = lambda file_path=None: {}
        mod.add_term = lambda list_id, term, note="", force=False: {}
        mod.remove_term = lambda list_id, term: {}
    if "word_lookup" in capabilities:
        mod.check_word = lambda word: {}
    if "checks" in capabilities:
        mod.list_checks = lambda: {c: {} for c in check_ids}
        mod.set_enabled_checks = lambda check_ids: None
        mod.set_checks_enabled = lambda states: None
    if "check_config" in capabilities:
        mod.list_check_config = lambda: {}
        mod.set_check_config = lambda check_id, threshold=None, action=None: None
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
    def _fake_registry(self, known_ids=("ste100",), modules=None):
        modules = modules or {rid: _fake_ruleset(rid) for rid in known_ids}
        return types.SimpleNamespace(
            get_ruleset=lambda rid: modules[rid] if rid in modules else (_ for _ in ()).throw(
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

    def test_preserves_every_extra_rule_key_not_only_packs(self):
        """A routing edit that says nothing about a rule's other keys
        must not drop them. Packs had this guarantee as a carve-out;
        "disable" was already exposed to the identical clobber, and
        "embedded_prose" would have been next."""
        import json
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            with open(path, "w") as f:
                json.dump({"rulesets": [
                    {"glob": "*.py", "ruleset": "ste100",
                     "embedded_prose": "ste100",
                     "disable": ["some_check"]},
                ]}, f)
            config.save_rules(tmp, [{"glob": "*.py", "ruleset": "ste100"}],
                               self._fake_registry(), config_file=path)
            with open(path) as f:
                rule = json.load(f)["rulesets"][0]
            self.assertEqual(rule["embedded_prose"], "ste100")
            self.assertEqual(rule["disable"], ["some_check"])

    def test_embedded_prose_typo_raises_before_writing(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            rules = [{"glob": "*.py", "ruleset": "ste100",
                      "embedded_prose": "slopwtch"}]
            with self.assertRaises(rulesets.UnknownRulesetError):
                config.save_rules(tmp, rules, self._fake_registry(),
                                   config_file=path)
            self.assertFalse(os.path.exists(path))

    def test_embedded_prose_on_an_extractorless_extension_raises(self):
        """A binding that can never fire is a gate quietly off -- the
        .dat-bypass failure shape, refused at write time."""
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            rules = [{"glob": "*.md", "ruleset": "ste100",
                      "embedded_prose": "ste100"}]
            with self.assertRaises(ValueError):
                config.save_rules(tmp, rules, self._fake_registry(),
                                   config_file=path)

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

    def test_changing_a_rules_ruleset_drops_packs_the_new_ruleset_never_heard_of(self):
        """The bug this guards: *.txt routed to ste100 (packs bound to its
        "project_terms" list), then a routing edit repoints it at
        slopwatch (no "project_terms" list at all) without touching
        packs -- the old packs must not survive as dead weight the new
        ruleset can never read."""
        import json
        import os
        import tempfile
        registry = self._fake_registry(modules={
            "ste100": _fake_ruleset("ste100", term_lists={"project_terms": {}}),
            "slopwatch": _fake_ruleset("slopwatch", term_lists={"terminology": {}}),
        })
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            with open(path, "w") as f:
                json.dump({"rulesets": [
                    {"glob": "*.txt", "ruleset": "ste100",
                     "packs": {"project_terms": ["mdn-glossary"]}},
                ]}, f)
            config.save_rules(tmp, [{"glob": "*.txt", "ruleset": "slopwatch"}],
                               registry, config_file=path)
            with open(path) as f:
                rule = json.load(f)["rulesets"][0]
            self.assertNotIn("packs", rule)

    def test_changing_a_rules_ruleset_keeps_packs_the_new_ruleset_still_has(self):
        import json
        import os
        import tempfile
        registry = self._fake_registry(modules={
            "codewatch": _fake_ruleset("codewatch", term_lists={"generic_naming": {}}),
            "slopwatch": _fake_ruleset("slopwatch", term_lists={"generic_naming": {}}),
        })
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            with open(path, "w") as f:
                json.dump({"rulesets": [
                    {"glob": "*.txt", "ruleset": "codewatch",
                     "packs": {"generic_naming": ["mdn-glossary"]}},
                ]}, f)
            config.save_rules(tmp, [{"glob": "*.txt", "ruleset": "slopwatch"}],
                               registry, config_file=path)
            with open(path) as f:
                rule = json.load(f)["rulesets"][0]
            self.assertEqual(rule["packs"], {"generic_naming": ["mdn-glossary"]})

    def test_changing_embedded_prose_drops_disable_entries_the_new_one_lacks(self):
        import json
        import os
        import tempfile
        registry = self._fake_registry(modules={
            "codewatch": _fake_ruleset("codewatch", capabilities=frozenset({"checks"}),
                                        check_ids=("todo_stub",)),
            "slopwatch": _fake_ruleset("slopwatch", capabilities=frozenset({"checks"}),
                                        check_ids=("colon_reveal",)),
            "ste100": _fake_ruleset("ste100", capabilities=frozenset({"checks"}),
                                     check_ids=("passive",)),
        })
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            with open(path, "w") as f:
                json.dump({"rulesets": [
                    {"glob": "*.py", "ruleset": "codewatch",
                     "embedded_prose": "slopwatch", "disable": ["colon_reveal"]},
                ]}, f)
            config.save_rules(
                tmp, [{"glob": "*.py", "ruleset": "codewatch", "embedded_prose": "ste100"}],
                registry, config_file=path)
            with open(path) as f:
                rule = json.load(f)["rulesets"][0]
            self.assertNotIn("disable", rule)  # colon_reveal belongs to neither codewatch nor ste100

    def test_unchanged_ruleset_never_revalidates_extras(self):
        """A routing edit that leaves ruleset and embedded_prose alone
        must not touch packs/disable at all, even against a registry that
        would call them all orphaned -- this path is "did anything that
        determines validity change", not "revalidate on every save"."""
        import json
        import os
        import tempfile
        registry = self._fake_registry(modules={"ste100": _fake_ruleset("ste100")})
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            with open(path, "w") as f:
                json.dump({"rulesets": [
                    {"glob": "*.md", "ruleset": "ste100",
                     "packs": {"project_terms": ["mdn-glossary"]},
                     "disable": ["some_check"]},
                ]}, f)
            config.save_rules(tmp, [{"glob": "*.md", "ruleset": "ste100"}],
                               registry, config_file=path)
            with open(path) as f:
                rule = json.load(f)["rulesets"][0]
            self.assertEqual(rule["packs"], {"project_terms": ["mdn-glossary"]})
            self.assertEqual(rule["disable"], ["some_check"])


class OrphanedRuleExtrasTests(unittest.TestCase):
    def _registry(self):
        return types.SimpleNamespace(get_ruleset=lambda rid: {
            "ste100": _fake_ruleset("ste100", term_lists={"project_terms": {}}),
            "slopwatch": _fake_ruleset("slopwatch", capabilities=frozenset({"checks"}),
                                        check_ids=("colon_reveal",),
                                        term_lists={"terminology": {}}),
            "codewatch": _fake_ruleset("codewatch", capabilities=frozenset({"checks"}),
                                        check_ids=("todo_stub",),
                                        term_lists={"generic_naming": {}}),
        }[rid])

    def test_no_config_file_returns_empty_list(self):
        self.assertEqual(
            config.orphaned_rule_extras(
                PROJECT_ROOT, self._registry(),
                config_file="/nonexistent/stopslop.config.json"),
            [])

    def test_a_pack_list_the_ruleset_never_declared_is_orphaned(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            with open(path, "w") as f:
                json.dump({"rulesets": [
                    {"glob": "*.txt", "ruleset": "slopwatch",
                     "packs": {"project_terms": ["mdn-glossary"]}},
                ]}, f)
            found = config.orphaned_rule_extras(tmp, self._registry(), config_file=path)
            self.assertEqual(found, [{"glob": "*.txt",
                                       "packs": {"project_terms": ["mdn-glossary"]}}])

    def test_a_pack_list_the_ruleset_does_declare_is_not_orphaned(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            with open(path, "w") as f:
                json.dump({"rulesets": [
                    {"glob": "*.md", "ruleset": "ste100",
                     "packs": {"project_terms": ["mdn-glossary"]}},
                ]}, f)
            self.assertEqual(config.orphaned_rule_extras(tmp, self._registry(), config_file=path), [])

    def test_a_disable_entry_only_the_embedded_ruleset_recognizes_is_not_orphaned(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            with open(path, "w") as f:
                json.dump({"rulesets": [
                    {"glob": "*.py", "ruleset": "codewatch", "embedded_prose": "slopwatch",
                     "disable": ["colon_reveal"]},
                ]}, f)
            self.assertEqual(config.orphaned_rule_extras(tmp, self._registry(), config_file=path), [])

    def test_a_disable_entry_no_invoked_ruleset_recognizes_is_orphaned(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            with open(path, "w") as f:
                json.dump({"rulesets": [
                    {"glob": "*.py", "ruleset": "codewatch", "disable": ["colon_reveal"]},
                ]}, f)
            found = config.orphaned_rule_extras(tmp, self._registry(), config_file=path)
            self.assertEqual(found, [{"glob": "*.py", "disable": ["colon_reveal"]}])

    def test_out_of_scope_rule_is_never_orphaned(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            with open(path, "w") as f:
                json.dump({"rulesets": [{"glob": ".claude/*", "ruleset": None}]}, f)
            self.assertEqual(config.orphaned_rule_extras(tmp, self._registry(), config_file=path), [])

    def test_prune_removes_only_the_orphaned_part_and_keeps_the_rest(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            with open(path, "w") as f:
                json.dump({"rulesets": [
                    {"glob": "*.txt", "ruleset": "slopwatch",
                     "packs": {"project_terms": ["mdn-glossary"], "terminology": ["nist-security"]}},
                ]}, f)
            removed = config.prune_orphaned_rule_extras(tmp, self._registry(), config_file=path)
            self.assertEqual(removed, [{"glob": "*.txt",
                                         "packs": {"project_terms": ["mdn-glossary"]}}])
            with open(path) as f:
                rule = json.load(f)["rulesets"][0]
            self.assertEqual(rule["packs"], {"terminology": ["nist-security"]})

    def test_prune_with_nothing_orphaned_is_a_no_op(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            with open(path, "w") as f:
                json.dump({"rulesets": [{"glob": "*.md", "ruleset": "ste100"}]}, f)
            self.assertEqual(config.prune_orphaned_rule_extras(tmp, self._registry(), config_file=path), [])


class SetRuleDisableTests(unittest.TestCase):
    """The per-rule "disable" list disabled_checks_for_path unions into
    every gate call -- writable through one function with the same
    guarantees as set_rule_packs: loud on an unknown glob or check id,
    and an empty list removes the key instead of writing an empty one."""

    def _write(self, tmp, rules):
        path = os.path.join(tmp, "stopslop.config.json")
        with open(path, "w") as f:
            json.dump({"rulesets": rules}, f)
        return path

    def test_round_trips_through_matching_rule(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, [{"glob": "*.py", "ruleset": "codewatch"}])
            config.set_rule_disable(tmp, "*.py", ["colon_reveal"], config_file=path)
            rule = config.matching_rule(os.path.join(tmp, "a.py"), tmp,
                                          config_file=path)
            self.assertEqual(rule["disable"], ["colon_reveal"])

    def test_empty_list_removes_the_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, [{"glob": "*.py", "ruleset": "codewatch",
                                        "disable": ["colon_reveal"]}])
            config.set_rule_disable(tmp, "*.py", [], config_file=path)
            with open(path) as f:
                rules = json.load(f)["rulesets"]
            self.assertNotIn("disable", rules[0])

    def test_unknown_glob_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, [{"glob": "*.py", "ruleset": "codewatch"}])
            with self.assertRaises(ValueError):
                config.set_rule_disable(tmp, "*.nope", ["x"], config_file=path)

    def test_unknown_check_id_raises_when_known_checks_given(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, [{"glob": "*.py", "ruleset": "codewatch"}])
            with self.assertRaises(ValueError):
                config.set_rule_disable(tmp, "*.py", ["not_a_check"],
                                          known_checks={"colon_reveal"},
                                          config_file=path)

    def test_preserves_every_other_rule_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, [
                {"glob": "*.py", "ruleset": "codewatch",
                 "embedded_prose": "slopwatch",
                 "packs": {"generic_naming": ["mdn-glossary"]}}])
            config.set_rule_disable(tmp, "*.py", ["colon_reveal"], config_file=path)
            with open(path) as f:
                rule = json.load(f)["rulesets"][0]
            self.assertEqual(rule["embedded_prose"], "slopwatch")
            self.assertEqual(rule["packs"], {"generic_naming": ["mdn-glossary"]})


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



class CheckConfigConfigTests(unittest.TestCase):
    """Per-check {threshold, action} overrides: ruleset -> check_id ->
    spec, since every check owns its own pair instead of one shared
    ruleset-wide number."""

    def test_no_config_file_returns_empty_dict(self):
        self.assertEqual(
            config.check_config(PROJECT_ROOT, "slopwatch",
                                 config_file="/nonexistent/stopslop.config.json"),
            {})

    def test_round_trips_through_save_and_load(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            config.save_check_config(tmp, "slopwatch", "em_dash_cluster",
                                      {"threshold": 5, "action": "block"}, config_file=path)
            self.assertEqual(
                config.check_config(tmp, "slopwatch", config_file=path),
                {"em_dash_cluster": {"threshold": 5, "action": "block"}})

    def test_a_second_check_does_not_clobber_the_first(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            config.save_check_config(tmp, "slopwatch", "em_dash_cluster",
                                      {"threshold": 5, "action": "block"}, config_file=path)
            config.save_check_config(tmp, "slopwatch", "vague_intensifier",
                                      {"threshold": 3, "action": "warn"}, config_file=path)
            saved = config.check_config(tmp, "slopwatch", config_file=path)
            self.assertEqual(saved["em_dash_cluster"], {"threshold": 5, "action": "block"})
            self.assertEqual(saved["vague_intensifier"], {"threshold": 3, "action": "warn"})

    def test_ruleset_not_mentioned_returns_empty_dict(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            config.save_check_config(tmp, "slopwatch", "em_dash_cluster",
                                      {"threshold": 5, "action": "block"}, config_file=path)
            self.assertEqual(config.check_config(tmp, "codewatch", config_file=path), {})

    def test_preserves_rulesets_key_already_in_the_file(self):
        import json
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            with open(path, "w") as f:
                json.dump({"rulesets": [{"glob": "*.md", "ruleset": "ste100"}]}, f)
            config.save_check_config(tmp, "slopwatch", "em_dash_cluster",
                                      {"threshold": 5, "action": "block"}, config_file=path)
            with open(path) as f:
                written = json.load(f)
            self.assertEqual(written["rulesets"], [{"glob": "*.md", "ruleset": "ste100"}])


class CustomTermListsConfigTests(unittest.TestCase):
    """A project's own term-list declarations, layered on top of a
    ruleset's code-defined TERM_LISTS -- see effective_term_lists()."""

    def test_no_config_file_returns_empty_dict(self):
        self.assertEqual(
            config.custom_term_lists(PROJECT_ROOT, "codewatch",
                                      config_file="/nonexistent/stopslop.config.json"),
            {})

    def test_round_trips_through_save_and_load(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            spec = {"label": "Jargon", "polarity": "deny", "accepts_additions": True,
                    "accepts_packs": False, "content_kind": "word"}
            config.save_custom_term_list(tmp, "codewatch", "jargon", spec, config_file=path)
            self.assertEqual(config.custom_term_lists(tmp, "codewatch", config_file=path),
                              {"jargon": spec})

    def test_a_second_list_does_not_clobber_the_first(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            config.save_custom_term_list(tmp, "codewatch", "jargon",
                                          {"label": "Jargon"}, config_file=path)
            config.save_custom_term_list(tmp, "codewatch", "acronyms",
                                          {"label": "Acronyms"}, config_file=path)
            saved = config.custom_term_lists(tmp, "codewatch", config_file=path)
            self.assertEqual(saved["jargon"], {"label": "Jargon"})
            self.assertEqual(saved["acronyms"], {"label": "Acronyms"})

    def test_ruleset_not_mentioned_returns_empty_dict(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            config.save_custom_term_list(tmp, "codewatch", "jargon",
                                          {"label": "Jargon"}, config_file=path)
            self.assertEqual(config.custom_term_lists(tmp, "slopwatch", config_file=path), {})

    def test_delete_removes_the_declaration(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            config.save_custom_term_list(tmp, "codewatch", "jargon",
                                          {"label": "Jargon"}, config_file=path)
            removed = config.delete_custom_term_list(tmp, "codewatch", "jargon", config_file=path)
            self.assertTrue(removed)
            self.assertEqual(config.custom_term_lists(tmp, "codewatch", config_file=path), {})

    def test_delete_of_unknown_list_returns_false(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            self.assertFalse(config.delete_custom_term_list(tmp, "codewatch", "nope", config_file=path))

    def test_delete_with_no_config_file_returns_false(self):
        self.assertFalse(config.delete_custom_term_list(
            PROJECT_ROOT, "codewatch", "nope", config_file="/nonexistent/stopslop.config.json"))


class AddCustomTermListTests(unittest.TestCase):
    """add_custom_term_list is the one shared validate-then-save path --
    the webui, the CLI, and the MCP server all call this instead of each
    re-deriving the same id-format/collision checks (see routes_vocabulary
    .py's add_list route, which used to carry this logic itself)."""

    def test_add_then_visible(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            spec = config.add_custom_term_list(tmp, "codewatch", "jargon", {}, config_file=path)
            self.assertEqual(spec["label"], "jargon")
            self.assertEqual(spec["polarity"], "deny")
            saved = config.custom_term_lists(tmp, "codewatch", config_file=path)
            self.assertIn("jargon", saved)

    def test_label_defaults_to_the_id_but_is_overridable(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            spec = config.add_custom_term_list(tmp, "codewatch", "jargon", {},
                                                label="Jargon", config_file=path)
            self.assertEqual(spec["label"], "Jargon")

    def test_refuses_a_malformed_id(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            with self.assertRaises(ValueError):
                config.add_custom_term_list(tmp, "codewatch", "Not-Valid", {}, config_file=path)

    def test_refuses_a_built_in_list_id(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            with self.assertRaises(ValueError):
                config.add_custom_term_list(tmp, "codewatch", "generic_naming",
                                             {"generic_naming": {}}, config_file=path)

    def test_refuses_re_adding_an_existing_custom_list(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            config.add_custom_term_list(tmp, "codewatch", "jargon", {}, config_file=path)
            with self.assertRaises(ValueError):
                config.add_custom_term_list(tmp, "codewatch", "jargon", {}, config_file=path)

    def test_an_invalid_polarity_falls_back_to_deny(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            spec = config.add_custom_term_list(tmp, "codewatch", "jargon", {},
                                                polarity="bogus", config_file=path)
            self.assertEqual(spec["polarity"], "deny")

    def test_feeds_lands_on_the_spec_when_given(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            spec = config.add_custom_term_list(tmp, "codewatch", "jargon", {},
                                                feeds="no_todo", config_file=path)
            self.assertEqual(spec["feeds"], "no_todo")

    def test_feeds_is_absent_by_default(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            spec = config.add_custom_term_list(tmp, "codewatch", "jargon", {}, config_file=path)
            self.assertNotIn("feeds", spec)


class SetCustomTermListFeedsTests(unittest.TestCase):
    def test_binds_an_existing_list(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            config.add_custom_term_list(tmp, "codewatch", "jargon", {}, config_file=path)
            spec = config.set_custom_term_list_feeds(tmp, "codewatch", "jargon", "no_todo",
                                                       config_file=path)
            self.assertEqual(spec["feeds"], "no_todo")
            self.assertEqual(config.custom_term_lists(tmp, "codewatch", config_file=path)
                              ["jargon"]["feeds"], "no_todo")

    def test_none_unbinds_it(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            config.add_custom_term_list(tmp, "codewatch", "jargon", {}, feeds="no_todo",
                                         config_file=path)
            spec = config.set_custom_term_list_feeds(tmp, "codewatch", "jargon", None,
                                                       config_file=path)
            self.assertNotIn("feeds", spec)

    def test_refuses_an_unknown_list(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            with self.assertRaises(ValueError):
                config.set_custom_term_list_feeds(tmp, "codewatch", "never_added", "no_todo",
                                                   config_file=path)

    def test_other_spec_fields_survive_a_rebind(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            config.add_custom_term_list(tmp, "codewatch", "jargon", {}, label="Jargon",
                                         config_file=path)
            spec = config.set_custom_term_list_feeds(tmp, "codewatch", "jargon", "no_todo",
                                                       config_file=path)
            self.assertEqual(spec["label"], "Jargon")


class ClearFeedsForCheckTests(unittest.TestCase):
    def test_unbinds_whichever_list_fed_the_removed_check(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            config.add_custom_term_list(tmp, "codewatch", "jargon", {}, feeds="no_todo",
                                         config_file=path)
            config.clear_feeds_for_check(tmp, "codewatch", "no_todo", config_file=path)
            self.assertNotIn("feeds", config.custom_term_lists(tmp, "codewatch", config_file=path)["jargon"])

    def test_a_check_with_nothing_bound_is_a_no_op(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            config.add_custom_term_list(tmp, "codewatch", "jargon", {}, config_file=path)
            config.clear_feeds_for_check(tmp, "codewatch", "no_todo", config_file=path)  # must not raise
            self.assertNotIn("feeds", config.custom_term_lists(tmp, "codewatch", config_file=path)["jargon"])

    def test_only_the_matching_list_is_unbound_others_survive(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            config.add_custom_term_list(tmp, "codewatch", "jargon", {}, feeds="no_todo",
                                         config_file=path)
            config.add_custom_term_list(tmp, "codewatch", "other", {}, feeds="another_check",
                                         config_file=path)
            config.clear_feeds_for_check(tmp, "codewatch", "no_todo", config_file=path)
            lists = config.custom_term_lists(tmp, "codewatch", config_file=path)
            self.assertNotIn("feeds", lists["jargon"])
            self.assertEqual(lists["other"]["feeds"], "another_check")


class CheckTermsListAvailableTests(unittest.TestCase):
    """The shared validate-before-write half of binding a custom check to
    a vocabulary list -- the CLI, the MCP server, and the webui all call
    this one function instead of each re-deriving the same conflict
    check (see webui/routes_checks.py, which used to carry a private
    copy of exactly this before it moved here)."""

    def test_an_unbound_list_is_available(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            config.add_custom_term_list(tmp, "codewatch", "jargon", {}, config_file=path)
            config.check_terms_list_available(tmp, "codewatch", "no_todo", "jargon",
                                                config_file=path)  # must not raise

    def test_a_list_already_bound_to_the_same_check_is_available(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            config.add_custom_term_list(tmp, "codewatch", "jargon", {}, feeds="no_todo",
                                         config_file=path)
            config.check_terms_list_available(tmp, "codewatch", "no_todo", "jargon",
                                                config_file=path)  # must not raise

    def test_a_list_bound_to_a_different_check_raises(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            config.add_custom_term_list(tmp, "codewatch", "jargon", {}, feeds="other_check",
                                         config_file=path)
            with self.assertRaises(ValueError):
                config.check_terms_list_available(tmp, "codewatch", "no_todo", "jargon",
                                                    config_file=path)

    def test_no_terms_list_never_raises(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            config.check_terms_list_available(tmp, "codewatch", "no_todo", None)  # must not raise
            config.check_terms_list_available(tmp, "codewatch", "no_todo", "")  # must not raise


class ApplyTermsListBindingTests(unittest.TestCase):
    def test_binds_the_list_to_the_check(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            config.add_custom_term_list(tmp, "codewatch", "jargon", {}, config_file=path)
            config.apply_terms_list_binding(tmp, "codewatch", "no_todo", "jargon", config_file=path)
            lists = config.custom_term_lists(tmp, "codewatch", config_file=path)
            self.assertEqual(lists["jargon"]["feeds"], "no_todo")

    def test_none_unbinds_whatever_the_check_used_to_feed(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            config.add_custom_term_list(tmp, "codewatch", "jargon", {}, feeds="no_todo",
                                         config_file=path)
            config.apply_terms_list_binding(tmp, "codewatch", "no_todo", None, config_file=path)
            lists = config.custom_term_lists(tmp, "codewatch", config_file=path)
            self.assertNotIn("feeds", lists["jargon"])

    def test_rebinding_moves_the_pointer_off_the_old_list(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            config.add_custom_term_list(tmp, "codewatch", "old_list", {}, feeds="no_todo",
                                         config_file=path)
            config.add_custom_term_list(tmp, "codewatch", "new_list", {}, config_file=path)
            config.apply_terms_list_binding(tmp, "codewatch", "no_todo", "new_list", config_file=path)
            lists = config.custom_term_lists(tmp, "codewatch", config_file=path)
            self.assertNotIn("feeds", lists["old_list"])
            self.assertEqual(lists["new_list"]["feeds"], "no_todo")


class EffectiveTermListsTests(unittest.TestCase):
    def test_merges_custom_onto_base(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            base = {"generic_naming": {"label": "Generic name stems"}}
            config.save_custom_term_list(tmp, "codewatch", "jargon",
                                          {"label": "Jargon"}, config_file=path)
            merged = config.effective_term_lists(base, "codewatch", tmp, config_file=path)
            self.assertEqual(set(merged), {"generic_naming", "jargon"})

    def test_a_custom_list_can_never_shadow_a_built_in_one(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            base = {"generic_naming": {"label": "The real one"}}
            config.save_custom_term_list(tmp, "codewatch", "generic_naming",
                                          {"label": "A shadow attempt"}, config_file=path)
            merged = config.effective_term_lists(base, "codewatch", tmp, config_file=path)
            self.assertEqual(merged["generic_naming"], {"label": "The real one"})

    def test_no_custom_lists_returns_base_unchanged(self):
        base = {"generic_naming": {"label": "Generic name stems"}}
        merged = config.effective_term_lists(
            base, "codewatch", PROJECT_ROOT, config_file="/nonexistent/stopslop.config.json")
        self.assertEqual(merged, base)


class StrayTopLevelKeysTests(unittest.TestCase):
    """A top-level config key nothing reads anymore -- a removed feature's
    old on-disk setting (the "options" capability's ruleset-wide
    threshold is the real example that motivated this) sitting there
    looking active while it tunes nothing."""

    def test_no_config_file_returns_empty_list(self):
        self.assertEqual(
            config.stray_top_level_keys(
                PROJECT_ROOT, config_file="/nonexistent/stopslop.config.json"),
            [])

    def test_every_known_key_is_not_stray(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            with open(path, "w") as f:
                json.dump({k: {} for k in config.KNOWN_TOP_LEVEL_KEYS}, f)
            self.assertEqual(config.stray_top_level_keys(tmp, config_file=path), [])

    def test_an_unread_key_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            with open(path, "w") as f:
                json.dump({"rulesets": [], "options": {"codewatch": {}}}, f)
            self.assertEqual(config.stray_top_level_keys(tmp, config_file=path), ["options"])

    def test_strip_removes_only_the_named_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            with open(path, "w") as f:
                json.dump({"rulesets": [{"glob": "*.md", "ruleset": "ste100"}],
                           "options": {"codewatch": {"block_flag_count_threshold": 3}},
                           "another_dead_key": 1}, f)
            config.strip_top_level_keys(tmp, ["options", "another_dead_key"], config_file=path)
            with open(path) as f:
                written = json.load(f)
            self.assertEqual(written, {"rulesets": [{"glob": "*.md", "ruleset": "ste100"}]})

    def test_strip_tolerates_a_key_already_gone(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            with open(path, "w") as f:
                json.dump({"rulesets": []}, f)
            config.strip_top_level_keys(tmp, ["options"], config_file=path)  # does not raise
            with open(path) as f:
                written = json.load(f)
            self.assertEqual(written, {"rulesets": []})


class ResolveRulesetIdDefaultRulesTests(unittest.TestCase):
    """resolve_ruleset_id() against DEFAULT_RULES (no config file) --
    slopwatch (prose) and codewatch (*.py) are the deliberate defaults,
    and ste100 reaches no file without a project saying so -- see
    DEFAULT_RULES's own docstring for why that reversed. This suite pins
    the current intentional shape so a *future* change is still a
    deliberate, reviewed edit here rather than silent drift."""

    CASES = [
        # Prose defaults to slopwatch everywhere now, at every depth. ste100
        # is opt-in, for procedural text a project routes to it by name --
        # nothing below resolves to it, and that is the point of this table.
        (PROJECT_ROOT + "/README.md", "slopwatch"),
        (PROJECT_ROOT + "/docs/README.md", "slopwatch"),
        (PROJECT_ROOT + "/notes.txt", "slopwatch"),
        (PROJECT_ROOT + "/notes.rst", "slopwatch"),
        (PROJECT_ROOT + "/docs/sub/dir/file.md", "slopwatch"),
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
            get_ruleset=lambda rid: _fake_ruleset(rid) if rid == "slopwatch" else (_ for _ in ()).throw(
                rulesets.UnknownRulesetError(rid)),
            UnknownRulesetError=rulesets.UnknownRulesetError,
        )
        # What this pins is that a resolved id reaches the registry and
        # comes back as a module. The id itself is whatever DEFAULT_RULES
        # says today, which for prose is slopwatch.
        mod = config.resolve_ruleset(PROJECT_ROOT + "/notes.md", PROJECT_ROOT, registry)
        self.assertEqual(mod.RULESET_ID, "slopwatch")

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


class PerPathDisabledChecksTests(unittest.TestCase):
    """A routing rule can turn a check off for the paths it matches.

    Whole-file exemption already existed -- routing a path to
    `"ruleset": null` -- but that is too blunt for the real case: codewatch
    denying its OWN test file, a fixture deliberately full of bad code. The
    fix wanted is "swallowed_exception does not apply to fixtures", not
    "stop checking this file at all". Symmetric with packs, which are
    already bound per routing rule for the same reason."""

    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.root = self._dir.name
        self.cfg = os.path.join(self.root, "stopslop.config.json")

    def tearDown(self):
        self._dir.cleanup()

    def _write(self, rules, disabled=None):
        data = {"rulesets": rules}
        if disabled:
            data["disabled_checks"] = disabled
        with open(self.cfg, "w") as f:
            json.dump(data, f)

    def _for(self, rel, ruleset="codewatch"):
        return config.disabled_checks_for_path(
            self.root, ruleset, os.path.join(self.root, rel), config_file=self.cfg)

    def test_a_rule_disables_a_check_only_on_its_own_paths(self):
        self._write([
            {"glob": "tests/*.py", "ruleset": "codewatch",
             "disable": ["swallowed_exception"]},
            {"glob": "*.py", "ruleset": "codewatch"},
        ])
        self.assertEqual(self._for("tests/a.py"), ["swallowed_exception"])
        self.assertEqual(self._for("src/a.py"), [])

    def test_it_unions_with_the_project_wide_list(self):
        self._write([{"glob": "*.py", "ruleset": "codewatch",
                       "disable": ["print_debug"]}],
                     disabled={"codewatch": ["todo_stub"]})
        self.assertEqual(self._for("a.py"), ["print_debug", "todo_stub"])

    def test_a_rule_cannot_re_enable_what_the_project_disabled(self):
        """Union, never subtraction. One direction keeps 'why did this not
        fire here?' answerable, and stops a rule silently switching back on
        something the project deliberately switched off."""
        self._write([{"glob": "*.py", "ruleset": "codewatch", "disable": []}],
                     disabled={"codewatch": ["todo_stub"]})
        self.assertEqual(self._for("a.py"), ["todo_stub"])

    def test_a_rule_for_a_different_ruleset_is_ignored(self):
        self._write([{"glob": "*.md", "ruleset": "ste100",
                       "disable": ["modal"]}])
        self.assertEqual(self._for("a.md", ruleset="codewatch"), [])

    def test_no_file_path_means_the_project_wide_list_only(self):
        self._write([{"glob": "*.py", "ruleset": "codewatch",
                       "disable": ["print_debug"]}],
                     disabled={"codewatch": ["todo_stub"]})
        self.assertEqual(
            config.disabled_checks_for_path(self.root, "codewatch",
                                             config_file=self.cfg), ["todo_stub"])

    def test_a_malformed_disable_value_contributes_nothing(self):
        # Same posture as _packs_of: a bad value in a hand-edited config
        # must never raise inside a live gate call.
        self._write([{"glob": "*.py", "ruleset": "codewatch", "disable": "oops"}])
        self.assertEqual(self._for("a.py"), [])

    def test_the_disable_list_reaches_the_embedded_prose_ruleset_too(self):
        """A rule's disable applies to every ruleset the rule invokes on
        its paths -- found on day one of dogfooding, when colon_reveal
        read code strings ("Usage:", "Not saved:") as 194 false
        positives that only a per-path disable could turn off."""
        self._write([{"glob": "*.py", "ruleset": "codewatch",
                       "embedded_prose": "slopwatch",
                       "disable": ["colon_reveal"]}])
        self.assertEqual(self._for("a.py", ruleset="slopwatch"),
                          ["colon_reveal"])
        self.assertEqual(self._for("a.py", ruleset="codewatch"),
                          ["colon_reveal"])
        self.assertEqual(self._for("a.py", ruleset="ste100"), [])


class DynamicDiscoveryTests(unittest.TestCase):
    """rulesets/__init__.py's registry is populated by scanning its own
    subpackages (_discover_and_register), not by a hardcoded import list
    -- this proves the discovery MECHANISM: a subpackage declaring
    RULESET_ID is found and validated through the same conformance gate
    RegistryConformanceTests exercises directly; one without RULESET_ID
    is silently skipped as a non-ruleset helper; a loose module (not a
    package) is skipped too, the same way __init__.py's own docstring
    says it should be. Runs against a synthetic temp directory added to
    sys.path, never the real rulesets/ package, so a bad fixture here
    can't pollute the real, process-wide registry every other test
    module relies on."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.pkg_root = self._tmp.name
        sys.path.insert(0, self.pkg_root)
        self._new_modules = []

    def tearDown(self):
        sys.path.remove(self.pkg_root)
        for name in self._new_modules:
            sys.modules.pop(name, None)
        self._tmp.cleanup()

    def _write_package(self, name, body):
        d = os.path.join(self.pkg_root, name)
        os.makedirs(d)
        with open(os.path.join(d, "__init__.py"), "w") as f:
            f.write(textwrap.dedent(body))
        self._new_modules.append(name)

    def _discover(self, expected_module_name):
        """The same ispkg-only, RULESET_ID-presence-only filter
        _discover_and_register uses, against a local registry dict via
        _register_into -- never the real rulesets._REGISTRY."""
        reg = types.SimpleNamespace(_REGISTRY={})
        found = []
        for info in sorted(pkgutil.iter_modules([self.pkg_root]), key=lambda i: i.name):
            if not info.ispkg:
                continue
            module = importlib.import_module(info.name)
            if hasattr(module, "RULESET_ID"):
                _register_into(reg, module)
                found.append(info.name)
        return found, reg._REGISTRY

    def test_real_registry_matches_expected_ruleset_set(self):
        # The compensating control for trading hardcoded imports away:
        # an accidental new ruleset (a stray directory, an experiment
        # left half-done) is still caught here, at test time, rather
        # than only being noticeable from a glance over __init__.py.
        self.assertEqual({m.RULESET_ID for m in rulesets.list_rulesets()},
                          {"ste100", "slopwatch", "codewatch"})

    def test_package_with_ruleset_id_is_discovered(self):
        self._write_package("fake_good_ruleset", """
            RULESET_ID = "fake_good"
            RULESET_NAME = "Fake Good"
            CAPABILITIES = frozenset()
            def lint_and_gate(text, *, context=None, file_path=None): return {}
            def blocking_semantic_flags(semantic_flags): return []
            def apply_mechanical_fixes(text, file_path=None): return text
        """)
        found, registry = self._discover("fake_good_ruleset")
        self.assertIn("fake_good_ruleset", found)
        self.assertIn("fake_good", registry)

    def test_package_without_ruleset_id_is_skipped(self):
        self._write_package("fake_helper_pkg", "SOME_CONSTANT = 1\n")
        found, registry = self._discover("fake_helper_pkg")
        self.assertNotIn("fake_helper_pkg", found)
        self.assertEqual(registry, {})

    def test_loose_module_is_not_treated_as_a_ruleset_package(self):
        with open(os.path.join(self.pkg_root, "fake_loose_module.py"), "w") as f:
            f.write('RULESET_ID = "fake_loose"\n')
        self._new_modules.append("fake_loose_module")
        found, registry = self._discover("fake_loose_module")
        self.assertNotIn("fake_loose_module", found)
        self.assertEqual(registry, {})

    def test_malformed_ruleset_id_package_raises_loudly(self):
        self._write_package("fake_broken_ruleset", """
            RULESET_ID = "fake_broken"
            RULESET_NAME = "Fake Broken"
            CAPABILITIES = frozenset()
            # missing lint_and_gate/blocking_semantic_flags/apply_mechanical_fixes
        """)
        with self.assertRaises(rulesets.InvalidRulesetError):
            self._discover("fake_broken_ruleset")


if __name__ == "__main__":
    unittest.main()


class PerRuleCheckConfigTests(unittest.TestCase):
    """Thresholds scoped to a routing rule, not just a ruleset.

    A threshold is not a property of a ruleset, it is a property of a
    ruleset applied to a KIND of file. Measurement made that concrete:
    the human band for a formatting check is not the same in reference
    documentation as in a changelog, so one number for both is wrong in
    one of them by construction.
    """

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "stopslop.config.json")

    def _write(self, rules, check_config=None):
        data = {"rulesets": rules}
        if check_config:
            data["check_config"] = check_config
        with open(self.path, "w") as f:
            json.dump(data, f)

    def _for(self, rel):
        return config.check_config_for_path(
            self.dir, "slopwatch", os.path.join(self.dir, rel),
            config_file=self.path)

    def test_a_rules_own_override_reaches_its_paths(self):
        self._write([{"glob": "*.md", "ruleset": "slopwatch",
                       "check_config": {"bold_density": {"threshold": 20}}}])
        self.assertEqual(self._for("a.md")["bold_density"]["threshold"], 20)

    def test_a_path_the_rule_does_not_match_is_unaffected(self):
        self._write([{"glob": "docs/*.md", "ruleset": "slopwatch",
                       "check_config": {"bold_density": {"threshold": 20}}},
                      {"glob": "*.md", "ruleset": "slopwatch"}])
        self.assertEqual(self._for("docs/a.md")["bold_density"]["threshold"], 20)
        self.assertEqual(self._for("a.md"), {})

    def test_it_layers_over_the_project_wide_entry_per_field(self):
        """Replacing the whole spec would mean naming a threshold
        silently reset that check's ACTION to the ruleset default --
        the kind of surprise nobody finds until a write is denied for a
        reason the config does not appear to state."""
        self._write([{"glob": "*.md", "ruleset": "slopwatch",
                       "check_config": {"bold_density": {"threshold": 20}}}],
                     check_config={"slopwatch": {"bold_density":
                                                   {"threshold": 8,
                                                    "action": "block"}}})
        spec = self._for("a.md")["bold_density"]
        self.assertEqual(spec["threshold"], 20)
        self.assertEqual(spec["action"], "block")

    def test_no_file_path_gives_the_project_wide_answer(self):
        self._write([{"glob": "*.md", "ruleset": "slopwatch",
                       "check_config": {"bold_density": {"threshold": 20}}}],
                     check_config={"slopwatch": {"bold_density": {"threshold": 8}}})
        got = config.check_config_for_path(self.dir, "slopwatch",
                                            config_file=self.path)
        self.assertEqual(got["bold_density"]["threshold"], 8)

    def test_a_malformed_per_rule_entry_is_ignored_not_fatal(self):
        self._write([{"glob": "*.md", "ruleset": "slopwatch",
                       "check_config": "not a dict"}])
        self.assertEqual(self._for("a.md"), {})

    def test_the_writer_edits_the_key_the_reader_reads(self):
        """The routing rules live under "rulesets". An earlier writer
        guessed "rules", so the command reported success, the file held
        the override, and the gate never saw it."""
        self._write([{"glob": "*.md", "ruleset": "slopwatch"}])
        config.save_rule_check_config(self.dir, "*.md", "bold_density",
                                       {"threshold": 12}, config_file=self.path)
        with open(self.path) as f:
            data = json.load(f)
        self.assertNotIn("rules", data)
        self.assertEqual(self._for("a.md")["bold_density"]["threshold"], 12)

    def test_an_empty_spec_clears_the_override(self):
        self._write([{"glob": "*.md", "ruleset": "slopwatch",
                       "check_config": {"bold_density": {"threshold": 12}}}])
        config.save_rule_check_config(self.dir, "*.md", "bold_density", {},
                                       config_file=self.path)
        self.assertEqual(self._for("a.md"), {})
        with open(self.path) as f:
            self.assertNotIn("check_config", json.load(f)["rulesets"][0])

    def test_writing_to_an_unknown_glob_raises(self):
        self._write([{"glob": "*.md", "ruleset": "slopwatch"}])
        with self.assertRaises(ValueError):
            config.save_rule_check_config(self.dir, "*.rst", "bold_density",
                                           {"threshold": 12},
                                           config_file=self.path)


class AtomicWriteTests(unittest.TestCase):
    """Config writes must be all-or-nothing.

    Every reader in this module treats unparseable JSON the same as a
    MISSING file, so a torn write silently reverts a project to built-in
    defaults -- a config that appears to vanish with no error anywhere.
    And the dashboard is a long-running process editing the same file the
    CLI edits; it has clobbered a CLI write twice in this project's
    history.
    """

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "stopslop.config.json")

    def test_a_write_that_fails_leaves_the_old_file_intact(self):
        """The failure this protects against: a reader arriving after a
        half-finished write sees a truncated file and reads it as no
        config at all."""
        with open(self.path, "w") as f:
            json.dump({"rulesets": [{"glob": "*.md", "ruleset": "slopwatch"}]}, f)
        unserialisable = {"rulesets": [{"glob": "*.md", "ruleset": object()}]}
        with self.assertRaises(TypeError):
            config._write_json(self.path, unserialisable)
        with open(self.path) as f:
            self.assertEqual(json.load(f)["rulesets"][0]["glob"], "*.md")

    def test_a_failed_write_leaves_no_temp_file_behind(self):
        with self.assertRaises(TypeError):
            config._write_json(self.path, {"x": object()})
        leftovers = [n for n in os.listdir(self.dir) if n.startswith(".stopslop-")]
        self.assertEqual(leftovers, [])

    def test_the_temp_file_is_written_beside_the_target(self):
        """os.replace is only atomic within one filesystem, and the
        system temp directory is frequently a different one."""
        seen = {}
        real = config.tempfile.mkstemp

        def spy(*args, **kwargs):
            seen["dir"] = kwargs.get("dir")
            return real(*args, **kwargs)

        config.tempfile.mkstemp = spy
        try:
            config._write_json(self.path, {"rulesets": []})
        finally:
            config.tempfile.mkstemp = real
        self.assertEqual(os.path.realpath(seen["dir"]),
                          os.path.realpath(self.dir))

    def test_a_successful_write_round_trips(self):
        data = {"rulesets": [{"glob": "*.rst", "ruleset": "slopwatch"}]}
        config._write_json(self.path, data)
        with open(self.path) as f:
            self.assertEqual(json.load(f), data)

    def test_no_writer_in_this_module_opens_the_target_directly(self):
        """A new writer added later must go through _write_json, or it
        reintroduces the torn-write and the race at once."""
        source = os.path.join(os.path.dirname(os.path.abspath(config.__file__)),
                               "config.py")
        with open(source) as f:
            text = f.read()
        self.assertNotIn('open(path, "w")', text)
