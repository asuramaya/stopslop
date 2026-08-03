"""Tests for core/terms.py -- the one term-list primitive that replaced
ste100's "glossary" and slopwatch/codewatch's "wordlists".

Two behaviours here are load-bearing enough to be worth naming, because
both were unenforced before and both fail SILENTLY when broken:

  * pack content is scoped to the path being written, not to the ruleset;
  * a pack may not introduce a term the owning ruleset forbids.

A regression in either produces a gate that still runs, still reports
"clean", and simply stops catching things.
"""
import json
import os
import tempfile
import unittest

from core import config, terms


def _spec(built_ins=(), polarity="deny", accepts_packs=False, pack_admissible=None):
    spec = {"label": "L", "polarity": polarity, "accepts_packs": accepts_packs,
            "built_ins": built_ins}
    if pack_admissible is not None:
        spec["pack_admissible"] = pack_admissible
    return spec


class ProjectLayerStorageTests(unittest.TestCase):
    def test_no_config_file_returns_empty(self):
        self.assertEqual(
            terms.project_terms("/nonexistent", "slopwatch", "marketing_cliche",
                                 config_file="/nonexistent/stopslop.config.json"),
            {})

    def test_round_trips(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            payload = {"reportedly": {"note": "found in a real false negative"}}
            terms.save_project_terms(tmp, "slopwatch", "weasel_attribution",
                                      payload, config_file=path)
            self.assertEqual(
                terms.project_terms(tmp, "slopwatch", "weasel_attribution", config_file=path),
                payload)

    def test_lists_and_rulesets_stay_independent(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            terms.save_project_terms(tmp, "slopwatch", "weasel_attribution",
                                      {"reportedly": {"note": ""}}, config_file=path)
            terms.save_project_terms(tmp, "codewatch", "generic_naming",
                                      {"widget": {"note": ""}}, config_file=path)
            self.assertEqual(
                list(terms.project_terms(tmp, "slopwatch", "weasel_attribution",
                                          config_file=path)), ["reportedly"])
            self.assertEqual(
                list(terms.project_terms(tmp, "codewatch", "generic_naming",
                                          config_file=path)), ["widget"])

    def test_preserves_other_top_level_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            with open(path, "w") as f:
                json.dump({"disabled_checks": {"slopwatch": ["colon_reveal"]}}, f)
            terms.save_project_terms(tmp, "slopwatch", "weasel_attribution",
                                      {"reportedly": {"note": ""}}, config_file=path)
            with open(path) as f:
                written = json.load(f)
            self.assertEqual(written["disabled_checks"], {"slopwatch": ["colon_reveal"]})


class LayerPrecedenceTests(unittest.TestCase):
    def test_project_layer_wins_over_built_in(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            terms.save_project_terms(tmp, "demo", "l",
                                      {"alpha": {"note": "mine"}}, config_file=path)
            layers = terms.resolve(_spec(built_ins={"alpha", "beta"}), tmp, "demo", "l",
                                    config_file=path)
            self.assertEqual(layers["effective"]["alpha"], {"note": "mine"})
            self.assertEqual(layers["effective"]["beta"], {})
            self.assertEqual(sorted(layers["effective"]), ["alpha", "beta"])

    def test_layers_are_reported_separately(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            terms.save_project_terms(tmp, "demo", "l", {"mine": {"note": ""}}, config_file=path)
            layers = terms.resolve(_spec(built_ins={"shipped"}), tmp, "demo", "l",
                                    config_file=path)
            self.assertEqual(sorted(layers["built_in"]), ["shipped"])
            self.assertEqual(sorted(layers["project"]), ["mine"])
            self.assertEqual(layers["packs"], {})

    def test_list_not_accepting_packs_never_loads_any(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            with open(path, "w") as f:
                json.dump({"rulesets": [{"glob": "*.md", "ruleset": "ste100",
                                          "packs": {"project_terms": ["nist-security"]}}]}, f)
            layers = terms.resolve(_spec(accepts_packs=False), tmp, "ste100",
                                    "project_terms",
                                    file_path=os.path.join(tmp, "a.md"), config_file=path)
            self.assertEqual(layers["packs"], {})


class PackScopingTests(unittest.TestCase):
    """A pack is domain content, so it follows the PATH, not the ruleset."""

    def _config(self, tmp, rules):
        path = os.path.join(tmp, "stopslop.config.json")
        with open(path, "w") as f:
            json.dump({"rulesets": rules}, f)
        return path

    def test_pack_applies_only_to_the_matching_glob(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._config(tmp, [
                {"glob": "docs/*.md", "ruleset": "ste100",
                 "packs": {"project_terms": ["nist-security"]}},
                {"glob": "*.md", "ruleset": "ste100"},
            ])
            spec = _spec(accepts_packs=True)
            in_docs = terms.resolve(spec, tmp, "ste100", "project_terms",
                                     file_path=os.path.join(tmp, "docs/a.md"),
                                     config_file=path)
            elsewhere = terms.resolve(spec, tmp, "ste100", "project_terms",
                                       file_path=os.path.join(tmp, "a.md"),
                                       config_file=path)
            self.assertGreater(len(in_docs["packs"]), 0)
            self.assertEqual(elsewhere["packs"], {})

    def test_pack_bound_to_one_list_does_not_leak_into_another(self):
        # The binding is per LIST, in config. Attaching nist-security to
        # ste100's project_terms must not pour security vocabulary into a
        # different list resolved for the same path.
        with tempfile.TemporaryDirectory() as tmp:
            path = self._config(tmp, [
                {"glob": "*.md", "ruleset": "ste100",
                 "packs": {"project_terms": ["nist-security"]}}])
            layers = terms.resolve(_spec(accepts_packs=True), tmp, "ste100",
                                    "some_other_list",
                                    file_path=os.path.join(tmp, "a.md"), config_file=path)
            self.assertEqual(layers["packs"], {})

    def test_the_same_pack_can_feed_a_second_ruleset(self):
        # Impossible while a pack named its own single (ruleset, list)
        # target: nist-security claimed ste100 and nothing else could read
        # it. A pack is now inert content that any list may be pointed at.
        with tempfile.TemporaryDirectory() as tmp:
            path = self._config(tmp, [
                {"glob": "*.md", "ruleset": "ste100",
                 "packs": {"project_terms": ["nist-security"]}},
                {"glob": "*.py", "ruleset": "codewatch",
                 "packs": {"generic_naming": ["nist-security"]}}])
            spec = _spec(accepts_packs=True)
            for target, rs, lid in ((os.path.join(tmp, "a.md"), "ste100", "project_terms"),
                                     (os.path.join(tmp, "a.py"), "codewatch", "generic_naming")):
                layers = terms.resolve(spec, tmp, rs, lid,
                                        file_path=target, config_file=path)
                self.assertGreater(len(layers["packs"]), 0,
                                    f"{rs}.{lid} got no pack content")

    def test_unknown_pack_id_in_config_is_survivable(self):
        # A typo must not take the gate down; it simply contributes nothing.
        with tempfile.TemporaryDirectory() as tmp:
            path = self._config(tmp, [
                {"glob": "*.md", "ruleset": "ste100",
                 "packs": {"project_terms": ["nist-securty"]}}])
            layers = terms.resolve(_spec(accepts_packs=True), tmp, "ste100",
                                    "project_terms",
                                    file_path=os.path.join(tmp, "a.md"), config_file=path)
            self.assertEqual(layers["packs"], {})


class PackAdmissibilityGuardTests(unittest.TestCase):
    """The invariant that used to live only in three build scripts."""

    def test_guard_rejects_and_reports_the_rejection(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            with open(path, "w") as f:
                json.dump({"rulesets": [{"glob": "*.md", "ruleset": "ste100",
                                          "packs": {"project_terms": ["nist-security"]}}]}, f)
            from core import glossary_packs
            a_real_pack_term = sorted(glossary_packs.load_pack_terms("nist-security"))[0]

            layers = terms.resolve(
                _spec(accepts_packs=True, pack_admissible=lambda t: t != a_real_pack_term),
                tmp, "ste100", "project_terms",
                file_path=os.path.join(tmp, "a.md"), config_file=path)

            self.assertNotIn(a_real_pack_term, layers["packs"])
            self.assertNotIn(a_real_pack_term, layers["effective"])
            self.assertEqual(layers["rejected"][a_real_pack_term], "nist-security")

    def test_guard_does_not_block_the_project_layer(self):
        # A human registration may override a prohibition -- deliberately,
        # with a reason. Only bulk imports are held to the guard.
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            terms.save_project_terms(tmp, "demo", "l",
                                      {"forbidden": {"note": "on the record"}},
                                      config_file=path)
            layers = terms.resolve(
                _spec(accepts_packs=True, pack_admissible=lambda t: t != "forbidden"),
                tmp, "demo", "l", config_file=path)
            self.assertIn("forbidden", layers["effective"])


class AddRemoveTermTests(unittest.TestCase):
    LISTS = {"l": _spec()}

    def test_add_then_remove_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            r = terms.add_term("demo", self.LISTS, tmp, "l", "Widget",
                                note="why", config_file=path)
            self.assertEqual(r["status"], "registered")
            self.assertEqual(
                terms.project_terms(tmp, "demo", "l", config_file=path),
                {"widget": {"note": "why"}})   # normalised to lower case

            r = terms.remove_term("demo", self.LISTS, tmp, "l", "widget", config_file=path)
            self.assertEqual(r["status"], "removed")
            self.assertEqual(terms.project_terms(tmp, "demo", "l", config_file=path), {})

    def test_adding_twice_is_a_no_op(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            terms.add_term("demo", self.LISTS, tmp, "l", "widget", config_file=path)
            r = terms.add_term("demo", self.LISTS, tmp, "l", "widget", config_file=path)
            self.assertEqual(r["status"], "no-op")

    def test_removing_an_unregistered_term_is_a_no_op(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            r = terms.remove_term("demo", self.LISTS, tmp, "l", "never", config_file=path)
            self.assertEqual(r["status"], "no-op")

    def test_unknown_list_id_raises_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            with self.assertRaises(terms.UnknownTermListError):
                terms.add_term("demo", self.LISTS, tmp, "nope", "x", config_file=path)
            self.assertFalse(os.path.exists(path))

    def test_empty_term_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            r = terms.add_term("demo", self.LISTS, tmp, "l", "   ", config_file=path)
            self.assertFalse(r["ok"])

    def test_validator_can_short_circuit(self):
        def refuse(term, force):
            return {"ok": False, "status": "refused", "message": "nope"}, {}
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            r = terms.add_term("demo", self.LISTS, tmp, "l", "x",
                                validator=refuse, config_file=path)
            self.assertEqual(r["status"], "refused")
            self.assertEqual(terms.project_terms(tmp, "demo", "l", config_file=path), {})

    def test_validator_metadata_is_stored_beside_the_note(self):
        def annotate(term, force):
            return None, {"overrides_unapproved": True}
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            terms.add_term("demo", self.LISTS, tmp, "l", "x", note="n",
                            validator=annotate, config_file=path)
            self.assertEqual(
                terms.project_terms(tmp, "demo", "l", config_file=path),
                {"x": {"overrides_unapproved": True, "note": "n"}})

    def test_force_is_passed_through_to_the_validator(self):
        seen = []

        def record(term, force):
            seen.append(force)
            return None, {}
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            terms.add_term("demo", self.LISTS, tmp, "l", "x", force=True,
                            validator=record, config_file=path)
            self.assertEqual(seen, [True])


class SubtractionTests(unittest.TestCase):
    """Until this existed the stack was union-only: a list could grow and
    never shrink. A built-in lives in a Python literal inside a ruleset and
    a pack lives in a shipped JSON file, so neither could be edited -- the
    only escape from one wrong word was disabling a whole check or
    detaching a whole pack. That is also why the UI could not honestly
    offer "remove" on most of the terms it displayed."""

    LISTS = {"l": _spec(built_ins={"alpha", "beta"})}

    def test_removing_a_built_in_suppresses_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            r = terms.remove_term("demo", self.LISTS, tmp, "l", "alpha", config_file=path)
            self.assertEqual(r["status"], "suppressed")
            layers = terms.resolve(self.LISTS["l"], tmp, "demo", "l", config_file=path)
            self.assertNotIn("alpha", layers["effective"])
            self.assertIn("beta", layers["effective"])
            self.assertEqual(layers["suppressed"]["alpha"], "built-in")

    def test_a_suppressed_built_in_can_be_restored(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            terms.remove_term("demo", self.LISTS, tmp, "l", "alpha", config_file=path)
            r = terms.add_term("demo", self.LISTS, tmp, "l", "alpha", config_file=path)
            self.assertEqual(r["status"], "restored")
            layers = terms.resolve(self.LISTS["l"], tmp, "demo", "l", config_file=path)
            self.assertIn("alpha", layers["effective"])
            self.assertEqual(layers["suppressed"], {})
            # Restoring lifts the tombstone rather than writing a project
            # term that shadows the built-in it came from.
            self.assertEqual(layers["project"], {})

    def test_removing_a_project_term_deletes_rather_than_suppresses(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            terms.add_term("demo", self.LISTS, tmp, "l", "mine", config_file=path)
            r = terms.remove_term("demo", self.LISTS, tmp, "l", "mine", config_file=path)
            self.assertEqual(r["status"], "removed")
            self.assertEqual(
                terms.project_terms(tmp, "demo", "l", config_file=path), {})

    def test_suppressing_twice_is_a_no_op(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            terms.remove_term("demo", self.LISTS, tmp, "l", "alpha", config_file=path)
            r = terms.remove_term("demo", self.LISTS, tmp, "l", "alpha", config_file=path)
            self.assertEqual(r["status"], "no-op")

    def test_removing_a_term_no_layer_supplies_is_a_no_op(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            r = terms.remove_term("demo", self.LISTS, tmp, "l", "never", config_file=path)
            self.assertEqual(r["status"], "no-op")
            self.assertFalse(os.path.exists(path))

    def test_a_pack_term_can_be_suppressed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            with open(path, "w") as f:
                json.dump({"rulesets": [{"glob": "*.md", "ruleset": "ste100",
                                          "packs": {"pl": ["nist-security"]}}]}, f)
            from core import glossary_packs
            word = sorted(glossary_packs.load_pack_terms("nist-security"))[0]
            lists = {"pl": _spec(accepts_packs=True)}
            target = os.path.join(tmp, "a.md")

            r = terms.remove_term("ste100", lists, tmp, "pl", word,
                                   file_path=target, config_file=path)
            self.assertEqual(r["status"], "suppressed")
            layers = terms.resolve(lists["pl"], tmp, "ste100", "pl",
                                    file_path=target, config_file=path)
            self.assertNotIn(word, layers["effective"])
            self.assertEqual(layers["suppressed"][word], "a pack")

    def test_a_stale_tombstone_is_reported_not_hidden(self):
        # The pack was detached (or the ruleset dropped the built-in) after
        # the term was suppressed. Harmless, but it should be visible so it
        # can be cleaned up rather than lingering unseen.
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            terms.save_project_terms(tmp, "demo", "l",
                                      {"gone": {"note": "x", "removed": True}},
                                      config_file=path)
            layers = terms.resolve(self.LISTS["l"], tmp, "demo", "l", config_file=path)
            self.assertEqual(layers["suppressed"]["gone"], "nothing")
            self.assertNotIn("gone", layers["effective"])

    def test_tombstones_never_appear_as_project_terms(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            terms.remove_term("demo", self.LISTS, tmp, "l", "alpha", config_file=path)
            layers = terms.resolve(self.LISTS["l"], tmp, "demo", "l", config_file=path)
            self.assertEqual(layers["project"], {})
            view = terms.list_term_lists("demo", self.LISTS, tmp, config_file=path)["l"]
            self.assertEqual(view["project_terms"], {})
            self.assertEqual(view["suppressed_count"], 1)
            self.assertEqual(view["effective_count"], 1)


class _FakeRegistry:
    def __init__(self, modules):
        self._modules = modules

    def list_rulesets(self):
        return self._modules


class TermIndexTests(unittest.TestCase):
    """The flat, tagged view the UI renders: one row per term, so a pack
    word is findable instead of being a number in a caption."""

    def _module(self):
        import types
        return types.SimpleNamespace(
            RULESET_ID="demo", CAPABILITIES=frozenset({"terms"}),
            TERM_LISTS={"l": _spec(built_ins={"alpha"}, polarity="allow")})

    def test_every_layer_becomes_a_tagged_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            terms.save_project_terms(tmp, "demo", "l", {"mine": {"note": "why"}},
                                      config_file=path)
            rows = terms.term_index(_FakeRegistry([self._module()]), tmp,
                                     config_file=path)
            by_term = {r["term"]: r for r in rows}
            self.assertEqual(by_term["alpha"]["source"], "built-in")
            self.assertEqual(by_term["mine"]["source"], "yours")
            self.assertEqual(by_term["mine"]["note"], "why")
            for row in rows:
                self.assertEqual(row["ruleset"], "demo")
                self.assertEqual(row["list"], "l")
                self.assertEqual(row["polarity"], "allow")

    def test_suppressed_terms_leave_the_index_and_enter_the_suppressed_view(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            registry = _FakeRegistry([self._module()])
            terms.remove_term("demo", self._module().TERM_LISTS, tmp, "l", "alpha",
                               config_file=path)
            self.assertEqual(terms.term_index(registry, tmp, config_file=path), [])
            supp = terms.suppressed_index(registry, tmp, config_file=path)
            self.assertEqual(supp[0]["term"], "alpha")
            self.assertEqual(supp[0]["was from"], "built-in")

    def test_a_ruleset_without_terms_contributes_nothing(self):
        import types
        mod = types.SimpleNamespace(RULESET_ID="x", CAPABILITIES=frozenset({"checks"}))
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(terms.term_index(_FakeRegistry([mod]), tmp), [])

    def test_real_rulesets_produce_a_row_for_every_effective_term(self):
        import rulesets
        from core import paths
        root = paths.find_project_root(terms.__file__)
        rows = terms.term_index(rulesets, root)
        total = 0
        for module in rulesets.list_rulesets():
            if "terms" not in module.CAPABILITIES:
                continue
            for list_id, spec in module.TERM_LISTS.items():
                total += len(terms.resolve(spec, root, module.RULESET_ID,
                                            list_id)["effective"])
        self.assertEqual(len(rows), total)
        self.assertTrue(any(r["source"] == "built-in" for r in rows))


class LegacyKeyMigrationTests(unittest.TestCase):
    def setUp(self):
        terms._migration_checked.clear()

    def test_wordlists_key_becomes_terms_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            payload = {"reportedly": {"note": "kept"}}
            with open(path, "w") as f:
                json.dump({"wordlists": {"slopwatch": {"weasel_attribution": payload}}}, f)

            self.assertTrue(terms.migrate_legacy_keys(tmp, config_file=path))
            with open(path) as f:
                written = json.load(f)
            self.assertNotIn("wordlists", written)
            self.assertEqual(written["terms"]["slopwatch"]["weasel_attribution"], payload)


class LegacyPackMigrationTests(unittest.TestCase):
    """The pack half migrates separately, because reshaping it needs a
    list id and only the resolving caller has one -- a pack carries no
    opinion about which list reads it."""

    def test_glossary_packs_key_becomes_per_rule_per_list_packs(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            with open(path, "w") as f:
                json.dump({
                    "rulesets": [{"glob": "*.md", "ruleset": "ste100"},
                                  {"glob": "*.py", "ruleset": "codewatch"}],
                    "glossary_packs": {"ste100": ["nist-security"]},
                }, f)

            terms.migrate_legacy_packs(tmp, "ste100", "project_terms", config_file=path)
            with open(path) as f:
                written = json.load(f)
            self.assertNotIn("glossary_packs", written)
            by_glob = {r["glob"]: r for r in written["rulesets"]}
            self.assertEqual(by_glob["*.md"].get("packs"),
                              {"project_terms": ["nist-security"]})
            self.assertNotIn("packs", by_glob["*.py"])

    def test_list_blind_per_rule_packs_get_bound_to_the_asking_list(self):
        # The intermediate shape: packs already on the rule, but a bare
        # list, because the pack itself still claimed a target.
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            with open(path, "w") as f:
                json.dump({"rulesets": [{"glob": "*.md", "ruleset": "ste100",
                                          "packs": ["mdn-glossary"]}]}, f)
            terms.migrate_legacy_packs(tmp, "ste100", "project_terms", config_file=path)
            with open(path) as f:
                written = json.load(f)
            self.assertEqual(written["rulesets"][0]["packs"],
                              {"project_terms": ["mdn-glossary"]})

    def test_migration_preserves_current_behaviour_for_every_matching_rule(self):
        # Project-wide before, so project-wide after -- narrowing is the
        # user's call, not the migration's.
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            with open(path, "w") as f:
                json.dump({
                    "rulesets": [{"glob": "docs/*.md", "ruleset": "ste100"},
                                  {"glob": "*.md", "ruleset": "ste100"}],
                    "glossary_packs": {"ste100": ["mdn-glossary"]},
                }, f)
            terms.migrate_legacy_packs(tmp, "ste100", "project_terms", config_file=path)
            for target in ("docs/a.md", "a.md"):
                self.assertEqual(
                    config.packs_for_path(tmp, os.path.join(tmp, target),
                                           list_id="project_terms", config_file=path),
                    ["mdn-glossary"])

    def test_another_rulesets_legacy_packs_are_left_for_its_own_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            with open(path, "w") as f:
                json.dump({
                    "rulesets": [{"glob": "*.md", "ruleset": "ste100"},
                                  {"glob": "*.py", "ruleset": "codewatch"}],
                    "glossary_packs": {"ste100": ["nist-security"],
                                        "codewatch": ["mdn-glossary"]},
                }, f)
            terms.migrate_legacy_packs(tmp, "ste100", "project_terms", config_file=path)
            with open(path) as f:
                written = json.load(f)
            self.assertEqual(written["glossary_packs"], {"codewatch": ["mdn-glossary"]})

    def test_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            with open(path, "w") as f:
                json.dump({"rulesets": [{"glob": "*.md", "ruleset": "ste100"}],
                            "glossary_packs": {"ste100": ["nist-security"]}}, f)
            self.assertTrue(terms.migrate_legacy_packs(
                tmp, "ste100", "project_terms", config_file=path))
            self.assertFalse(terms.migrate_legacy_packs(
                tmp, "ste100", "project_terms", config_file=path))

    def test_no_config_file_is_a_no_op(self):
        self.assertFalse(terms.migrate_legacy_packs(
            "/nonexistent", "ste100", "project_terms",
            config_file="/nonexistent/stopslop.config.json"))

    def test_already_migrated_content_is_never_clobbered(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            with open(path, "w") as f:
                json.dump({
                    "terms": {"slopwatch": {"l": {"new": {"note": "current"}}}},
                    "wordlists": {"slopwatch": {"l": {"old": {"note": "stale"}}}},
                }, f)
            terms.migrate_legacy_keys(tmp, config_file=path)
            self.assertEqual(
                terms.project_terms(tmp, "slopwatch", "l", config_file=path),
                {"new": {"note": "current"}})

    def test_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            with open(path, "w") as f:
                json.dump({"wordlists": {"a": {"l": {"t": {"note": ""}}}}}, f)
            terms.migrate_legacy_keys(tmp, config_file=path)
            with open(path) as f:
                first = f.read()
            self.assertFalse(terms.migrate_legacy_keys(tmp, config_file=path))
            with open(path) as f:
                self.assertEqual(f.read(), first)

    def test_no_config_file_is_a_no_op(self):
        self.assertFalse(terms.migrate_legacy_keys(
            "/nonexistent", config_file="/nonexistent/stopslop.config.json"))

    def test_malformed_config_is_survivable(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            with open(path, "w") as f:
                f.write("{not json")
            self.assertFalse(terms.migrate_legacy_keys(tmp, config_file=path))

    def test_reading_terms_triggers_the_migration_lazily(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            with open(path, "w") as f:
                json.dump({"wordlists": {"slopwatch": {"l": {"t": {"note": "x"}}}}}, f)
            # Nothing called migrate_legacy_keys explicitly.
            self.assertEqual(
                terms.project_terms(tmp, "slopwatch", "l", config_file=path),
                {"t": {"note": "x"}})


class ListTermListsViewTests(unittest.TestCase):
    def test_reports_polarity_and_per_layer_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            terms.save_project_terms(tmp, "demo", "l", {"mine": {"note": ""}},
                                      config_file=path)
            view = terms.list_term_lists(
                "demo", {"l": _spec(built_ins={"a", "b", "c"}, polarity="allow")},
                tmp, config_file=path)["l"]
            self.assertEqual(view["polarity"], "allow")
            self.assertEqual(view["built_in_count"], 3)
            self.assertEqual(view["project_count"], 1)
            self.assertEqual(view["effective_count"], 4)
            self.assertEqual(view["project_terms"], {"mine": {"note": ""}})



class ClosedListTests(unittest.TestCase):
    """A list can be closed to NEW words while staying open to suppression
    and restore.

    ste100 used to enforce this by raising UnknownTermListError from its own
    add_term/remove_term for anything but project_terms -- two untruths at
    once (the list is declared right there in TERM_LISTS, and the caller had
    done nothing wrong), and it opted the one ruleset with a real external
    standard out of the shared primitive. Once the Configure page began
    rendering every declared list, that raise became a live crash on a
    visible button. Nothing in the suite covered it."""

    LISTS = {
        "shipped": {"polarity": "allow", "accepts_additions": False,
                     "built_ins": {"alpha": {}, "bravo": {}}},
        "mine": {"polarity": "allow", "built_ins": {}},
    }

    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.root = self._dir.name
        self.cfg = os.path.join(self.root, "stopslop.config.json")

    def tearDown(self):
        self._dir.cleanup()

    def _effective(self, list_id):
        return terms.resolve(self.LISTS[list_id], self.root, "demo", list_id,
                              config_file=self.cfg)

    def _add(self, list_id, term):
        return terms.add_term("demo", self.LISTS, self.root, list_id, term,
                               config_file=self.cfg)

    def _remove(self, list_id, term):
        return terms.remove_term("demo", self.LISTS, self.root, list_id, term,
                                  config_file=self.cfg)

    def test_a_closed_list_refuses_a_new_word_without_raising(self):
        result = self._add("shipped", "charlie")
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "refused")
        self.assertIn("shipped reference data", result["message"])
        self.assertNotIn("charlie", self._effective("shipped")["effective"])

    def test_a_closed_list_still_allows_suppression(self):
        self.assertEqual(self._remove("shipped", "alpha")["status"], "suppressed")
        layers = self._effective("shipped")
        self.assertNotIn("alpha", layers["effective"])
        self.assertIn("alpha", layers["suppressed"])

    def test_a_suppressed_word_can_be_restored_on_a_closed_list(self):
        """The bug this ordering exists to prevent. Gating restore behind
        the accepts_additions check made a closed list a one-way door:
        suppress a dictionary word and it could never come back, silently
        breaking the restorability the subtraction model promises."""
        self._remove("shipped", "alpha")
        result = self._add("shipped", "alpha")
        self.assertTrue(result["ok"], result.get("message"))
        self.assertEqual(result["status"], "restored")
        self.assertIn("alpha", self._effective("shipped")["effective"])

    def test_an_open_list_is_unaffected(self):
        self.assertEqual(self._add("mine", "delta")["status"], "registered")
        self.assertIn("delta", self._effective("mine")["effective"])


class EveryDeclaredListIsUsableTests(unittest.TestCase):
    """Whatever a ruleset declares in TERM_LISTS, the Configure page renders
    -- so every declared list must answer add and remove with a STATUS
    rather than an exception. A ruleset may refuse; it may not crash."""

    def test_no_declared_list_raises_on_add_or_remove(self):
        import rulesets as registry
        root = tempfile.mkdtemp()
        open(os.path.join(root, "stopslop.py"), "w").close()
        cfg = os.path.join(root, "stopslop.config.json")
        for module in registry.list_rulesets():
            if "terms" not in module.CAPABILITIES:
                continue
            for list_id in module.TERM_LISTS:
                with self.subTest(list=f"{module.RULESET_ID}.{list_id}"):
                    added = terms.add_term(module.RULESET_ID, module.TERM_LISTS,
                                            root, list_id, "zzprobezz",
                                            config_file=cfg)
                    self.assertIn("status", added)
                    removed = terms.remove_term(module.RULESET_ID, module.TERM_LISTS,
                                                 root, list_id, "zzprobezz",
                                                 config_file=cfg)
                    self.assertIn("status", removed)
if __name__ == "__main__":
    unittest.main()
