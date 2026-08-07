"""Static ruleset registry.

Rulesets are discovered by explicit import and registration at the bottom of
this file -- not by filesystem scanning. Adding a ruleset means adding one
import and one `_register()` call, kept deliberately manual so "what
rulesets exist" stays a single, git-diffable fact instead of "whatever
happens to be sitting in this directory." Revisit if a third or fourth
ruleset makes that manual step tedious.

Every ruleset module must expose the required contract surface below --
checked here at registration time (import time), not on first use, so a
malformed ruleset fails loudly at startup rather than surfacing as a
confusing error deep inside a live gate decision.
"""

# lint_and_gate(text, *, context=None, file_path=None) and
# apply_mechanical_fixes(text, file_path=None). file_path is part of the
# contract, not an optimisation: vocabulary packs attach to the routing
# rule that matched the path, so two files handled by the SAME ruleset can
# have genuinely different effective vocabularies. A ruleset that ignores
# file_path is fine; one that cannot accept it will break the live gate.
REQUIRED_ATTRS = (
    "RULESET_ID", "RULESET_NAME", "CAPABILITIES",
    "lint_and_gate", "blocking_semantic_flags", "apply_mechanical_fixes",
)

# Which extra attributes a declared CAPABILITIES entry obligates a ruleset
# to provide. A ruleset with no term lists at all simply omits "terms" from
# CAPABILITIES and implements none of these -- no stub methods required.
#
# "checks"/"options" were, until now, informal: every ruleset happened to
# expose list_checks()/set_enabled_checks() (or not) and callers guessed
# with hasattr() across stopslop.py/dashboard.py/mcp_server.py, with
# nothing to stop a ruleset from declaring half a contract (e.g.
# list_checks with no set_enabled_checks) and only finding out the hard
# way, deep inside a live call. Promoted to real, registry-enforced
# capabilities -- the actual inconsistency across ste100/slopwatch/
# codewatch was in the CONTRACT, not just in which checks each shipped.
#
# "terms" replaces what used to be TWO capabilities: "glossary"
# (register_term/unregister_term/list_terms, ste100 only) and "wordlists"
# (add_wordlist_term/remove_wordlist_term/list_wordlists, slopwatch and
# codewatch). Those were never different concepts -- only different
# POLARITIES of one concept, allow vs deny, given different names because
# ste100 was written first. See core/terms.py for the full argument and for
# the layered built_in -> packs -> project model that replaced both.
#
# Vocabulary PACKS are deliberately NOT in this table. A pack is enabled on
# a path glob, not on a ruleset (core.config.set_rule_packs), so pack
# enablement is a project-config operation with no ruleset method behind
# it -- which is precisely how the old list_glossary_packs/
# set_enabled_glossary_packs pair managed to sit on ste100 unregistered,
# with three separate callers hasattr()-guessing for them, for as long as
# it did.
# "checks" obligates BOTH write shapes, on purpose. set_enabled_checks
# replaces a ruleset's whole enabled set ("these and only these"), which is
# what a caller holding the full picture means; set_checks_enabled merges
# ("turn these ones on/off, leave the rest"), which is what a caller holding
# a partial view means. A ruleset offering only the replace form invites the
# bug the dashboard actually shipped -- a filtered table saved as if it were
# the whole list, disabling 18 of 20 checks silently. Both or neither.
CAPABILITY_ATTRS = {
    "terms": ("list_term_lists", "add_term", "remove_term"),
    "word_lookup": ("check_word",),
    "checks": ("list_checks", "set_enabled_checks", "set_checks_enabled"),
    "options": ("list_options", "set_options"),
    "check_config": ("list_check_config", "set_check_config"),
}


class UnknownRulesetError(Exception):
    pass


class InvalidRulesetError(Exception):
    """A module was registered but doesn't satisfy the contract."""


_REGISTRY = {}


def _register(module):
    missing = [a for a in REQUIRED_ATTRS if not hasattr(module, a)]
    if missing:
        raise InvalidRulesetError(
            f"ruleset module {module.__name__!r} is missing required "
            f"attribute(s): {missing}")
    for cap in module.CAPABILITIES:
        cap_missing = [a for a in CAPABILITY_ATTRS.get(cap, ()) if not hasattr(module, a)]
        if cap_missing:
            raise InvalidRulesetError(
                f"ruleset module {module.__name__!r} declares capability "
                f"{cap!r} but is missing: {cap_missing}")
    if module.RULESET_ID in _REGISTRY:
        raise InvalidRulesetError(
            f"ruleset id {module.RULESET_ID!r} is already registered "
            f"(by {_REGISTRY[module.RULESET_ID].__name__!r})")
    _REGISTRY[module.RULESET_ID] = module


def get_ruleset(ruleset_id):
    try:
        return _REGISTRY[ruleset_id]
    except KeyError:
        raise UnknownRulesetError(
            f"no ruleset registered as {ruleset_id!r} -- known: {sorted(_REGISTRY)}")


def list_rulesets():
    return [_REGISTRY[k] for k in sorted(_REGISTRY)]


# --- Registration -----------------------------------------------------
from rulesets import ste100 as _ste100
_register(_ste100)

from rulesets import slopwatch as _slopwatch
_register(_slopwatch)

from rulesets import codewatch as _codewatch
_register(_codewatch)
