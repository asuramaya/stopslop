"""Dynamic ruleset registry.

Rulesets are discovered by scanning this package's own subpackages (see
_discover_and_register at the bottom of this file), not by a hand-
maintained import list. A new ruleset is a new directory under
rulesets/ exposing the required contract below -- nothing here needs
editing to pick it up.

This traded away a previously deliberate choice: hardcoded imports kept
"what rulesets exist" a single, git-diffable fact rather than "whatever
happens to be sitting in this directory." The compensating control is
test_config.py's own pinning test, asserting today's real registry
still resolves to exactly {"ste100", "slopwatch", "codewatch"} -- so an
accidental new ruleset (a stray directory, an experiment left half-done)
is still caught, just at test time instead of at a glance over this file.

Every ruleset module must still expose the required contract surface
below -- checked here at registration time (import time), not on first
use, so a malformed ruleset fails loudly at startup rather than
surfacing as a confusing error deep inside a live gate decision. A
subpackage with no RULESET_ID is silently skipped as a non-ruleset
helper (there are none today, but core/ style shared code could
plausibly live under rulesets/ in the future); one that declares
RULESET_ID but fails the rest of the contract still raises loudly.
"""
import importlib
import pkgutil

from core import custom_rulesets as _custom_rulesets, paths as _paths

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
# "checks" was, until now, informal: every ruleset happened to expose
# list_checks()/set_enabled_checks() (or not) and callers guessed with
# hasattr() across stopslop.py/dashboard.py/mcp_server.py, with nothing
# to stop a ruleset from declaring half a contract (e.g. list_checks with
# no set_enabled_checks) and only finding out the hard way, deep inside a
# live call. Promoted to real, registry-enforced capabilities -- the
# actual inconsistency across ste100/slopwatch/codewatch was in the
# CONTRACT, not just in which checks each shipped. ("options", the old
# ruleset-wide tunables dict, died when ste100 -- its last user --
# migrated to per-check "check_config" like the other two.)
#
# "terms" is one capability, not two: ste100's allow list and slopwatch's/
# codewatch's deny lists are never different concepts, only different
# POLARITIES of one concept. See core/terms.py for the full argument and
# for the layered built_in -> packs -> project model behind it.
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
    "check_config": ("list_check_config", "set_check_config"),
    # A custom check is a real Python file under
    # .claude/stopslop/custom_checks/<ruleset_id>/ -- see core/custom_checks.py.
    # custom_check_units() names which core.checks.Unit values THIS
    # ruleset accepts (what "sentence"/"line"/"document" even mean is
    # ruleset-specific past the safe default -- see that module's own
    # docstring), so the dashboard's "Add check" form can only ever offer
    # a unit that will actually load.
    "custom_checks": ("custom_check_ids", "add_custom_check", "remove_custom_check",
                       "update_custom_check", "custom_check_units"),
}


class UnknownRulesetError(Exception):
    pass


class InvalidRulesetError(Exception):
    """A module was registered but doesn't satisfy the contract."""


_REGISTRY = {}
# Which ids came from .claude/stopslop/custom_rulesets/ rather than a
# built-in subpackage of this package -- the only thing unregister_ruleset()
# below is ever allowed to remove.
_CUSTOM_RULESET_IDS = set()


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


def is_custom_ruleset(ruleset_id):
    """Whether `ruleset_id` came from .claude/stopslop/custom_rulesets/
    rather than a built-in subpackage -- the public read of
    _CUSTOM_RULESET_IDS, for a caller (the webui) that needs to offer
    "Remove" for a custom ruleset and never for a built-in one."""
    return ruleset_id in _CUSTOM_RULESET_IDS


def unregister_ruleset(ruleset_id):
    """Remove one CUSTOM ruleset from the live registry -- called right
    after core.custom_rulesets.remove_ruleset() deletes its files, so a
    removed ruleset disappears from every picker in this same process,
    with no restart. Refuses for a built-in (or an unknown id) -- there
    is no file for either of those to have lost, so "unregister" would
    either corrupt the registry or silently do nothing surprising."""
    if ruleset_id not in _REGISTRY:
        raise UnknownRulesetError(f"no ruleset registered as {ruleset_id!r}")
    if ruleset_id not in _CUSTOM_RULESET_IDS:
        raise InvalidRulesetError(f"{ruleset_id!r} is a built-in ruleset -- it cannot be removed")
    del _REGISTRY[ruleset_id]
    _CUSTOM_RULESET_IDS.discard(ruleset_id)


def rescan_custom_rulesets():
    """Pick up a ruleset scaffolded since this process started, with no
    restart -- see core/custom_rulesets.py. Built-ins are untouched; this
    only re-runs the custom-directory half of _discover_and_register(),
    and only for an id not already registered (scaffold_ruleset() itself
    already refused any collision at write time -- this is belt-and-
    suspenders, the same posture core.custom_checks.effective_checks_table
    takes for its own merge)."""
    _discover_custom_rulesets()


# --- Discovery ----------------------------------------------------------

def _discover_custom_rulesets():
    try:
        project_root = _paths.find_project_root(__file__)
    except Exception:
        return
    for ruleset_id in _custom_rulesets.custom_ruleset_ids(project_root):
        if ruleset_id in _REGISTRY:
            continue
        module = _custom_rulesets.load_ruleset_module(project_root, ruleset_id)
        _register(module)
        _CUSTOM_RULESET_IDS.add(ruleset_id)


def _discover_and_register():
    """Import every direct subpackage of rulesets/ and register any that
    declares RULESET_ID, sorted by name for deterministic registration
    order. Runs once, at import time of this module -- a fresh process
    always sees the real current contents of the directory, and a
    malformed ruleset still fails at startup, not mid-gate. Also scans
    .claude/stopslop/custom_rulesets/ for a project's own scaffolded
    rulesets, AFTER every built-in has already registered -- a custom id
    colliding with a built-in one raises from _register()'s own already-
    registered check, the same as any other id collision here."""
    for info in sorted(pkgutil.iter_modules(__path__), key=lambda i: i.name):
        if not info.ispkg:
            continue
        module = importlib.import_module(f"{__name__}.{info.name}")
        if hasattr(module, "RULESET_ID"):
            _register(module)
    _discover_custom_rulesets()


_discover_and_register()
