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

REQUIRED_ATTRS = (
    "RULESET_ID", "RULESET_NAME", "CAPABILITIES",
    "lint_and_gate", "blocking_semantic_flags", "apply_mechanical_fixes",
)

# Which extra attributes a declared CAPABILITIES entry obligates a ruleset
# to provide. A ruleset with no glossary concept (e.g. a pattern-only
# ruleset with no closed vocabulary) simply omits "glossary" from
# CAPABILITIES and implements none of these -- no stub methods required.
CAPABILITY_ATTRS = {
    "glossary": ("register_term", "unregister_term", "list_terms"),
    "word_lookup": ("check_word",),
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
