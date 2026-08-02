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
    mod.lint_and_gate = lambda text, context=None: {"mechanical": [], "semantic": []}
    mod.blocking_semantic_flags = lambda semantic_flags: []
    mod.apply_mechanical_fixes = lambda text: text
    if "glossary" in capabilities:
        mod.register_term = lambda word, note="", override_unapproved=None: {}
        mod.unregister_term = lambda word: {}
        mod.list_terms = lambda: {}
    if "word_lookup" in capabilities:
        mod.check_word = lambda word: {}
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
        mod = _fake_ruleset("demo", capabilities=frozenset({"glossary"}))
        del mod.unregister_term
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


class GlossaryPacksConfigTests(unittest.TestCase):
    def test_no_config_file_returns_empty(self):
        self.assertEqual(
            config.enabled_glossary_packs(PROJECT_ROOT, "ste100",
                                           config_file="/nonexistent/stopslop.config.json"),
            [])

    def test_round_trips_through_save_and_load(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            config.save_glossary_packs(tmp, "ste100", ["microsoft-style-guide", "mdn-glossary"],
                                        config_file=path)
            self.assertEqual(
                config.enabled_glossary_packs(tmp, "ste100", config_file=path),
                ["microsoft-style-guide", "mdn-glossary"])

    def test_ruleset_not_mentioned_returns_empty(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            config.save_glossary_packs(tmp, "ste100", ["microsoft-style-guide"], config_file=path)
            self.assertEqual(
                config.enabled_glossary_packs(tmp, "some_other_ruleset", config_file=path), [])

    def test_preserves_rulesets_key_already_in_the_file(self):
        import json
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            with open(path, "w") as f:
                json.dump({"rulesets": [{"glob": "*.md", "ruleset": "ste100"}]}, f)
            config.save_glossary_packs(tmp, "ste100", ["mdn-glossary"], config_file=path)
            with open(path) as f:
                written = json.load(f)
            self.assertEqual(written["rulesets"], [{"glob": "*.md", "ruleset": "ste100"}])


class ResolveRulesetIdDefaultRulesTests(unittest.TestCase):
    """Required invariant: resolve_ruleset_id() against DEFAULT_RULES (no
    config file) must reproduce exactly what pretool_hook.py's old,
    pre-ruleset in_scope() truth table returned -- a ruleset existing in the
    registry must never change behavior for an unconfigured clone."""

    CASES = [
        (PROJECT_ROOT + "/README.md", "ste100"),
        (PROJECT_ROOT + "/notes.txt", "ste100"),
        (PROJECT_ROOT + "/notes.rst", "ste100"),
        (PROJECT_ROOT + "/docs/sub/dir/file.md", "ste100"),
        (PROJECT_ROOT + "/script.py", None),
        (PROJECT_ROOT + "/data.json", None),
        (PROJECT_ROOT + "/README.MD", None),          # case-sensitive, matches old .endswith()
        (PROJECT_ROOT + "/.claude/settings.local.json", None),
        (PROJECT_ROOT + "/.claude/notes.md", None),     # under .claude/ even though .md
        (PROJECT_ROOT + "/.claude/sub/deep.md", None),
        ("/some/other/repo/outside.md", None),           # outside project root entirely
    ]

    def test_default_rules_truth_table(self):
        for file_path, expected in self.CASES:
            with self.subTest(file_path=file_path):
                self.assertEqual(
                    config.resolve_ruleset_id(file_path, PROJECT_ROOT), expected)

    def test_no_config_file_never_resolves_to_a_non_default_id(self):
        # Guards against the registry growing a second ruleset (e.g.
        # "slopwatch") silently changing what an unconfigured clone lints
        # against -- only ids DEFAULT_RULES itself names are reachable here.
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
        mod = config.resolve_ruleset(PROJECT_ROOT + "/README.md", PROJECT_ROOT, registry)
        self.assertEqual(mod.RULESET_ID, "ste100")

    def test_out_of_scope_path_returns_none_without_touching_registry(self):
        registry = types.SimpleNamespace(
            get_ruleset=lambda rid: (_ for _ in ()).throw(AssertionError("should not be called")),
        )
        result = config.resolve_ruleset(PROJECT_ROOT + "/script.py", PROJECT_ROOT, registry)
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


class KnownExtensionsTests(unittest.TestCase):
    def test_default_extensions(self):
        self.assertEqual(config.known_extensions(PROJECT_ROOT,
                          config_file="/nonexistent/stopslop.config.json"),
                          {".md", ".txt", ".rst"})


if __name__ == "__main__":
    unittest.main()
