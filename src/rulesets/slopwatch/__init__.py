"""Contract surface for the slopwatch ruleset -- see lint.py for the actual
checks and the module docstring there for why this ruleset exists (proving
stopslop's plugin contract generalizes beyond ASD-STE100).

CAPABILITIES has no "word_lookup": slopwatch has no real external standard
to look a single word up against, so it implements none of that contract --
proof the optional-capability design needs no stub methods for a ruleset
that doesn't use them.

It DOES have "terms". Five of its checks (weasel_attribution,
marketing_adjective, filler_verb, marketing_cliche, stock_adverb) are
fundamentally "match text against a list of words or phrases", and a
project can extend any of them. That used to be a separate capability
called "wordlists", distinct from ste100's "glossary" -- but the two were
never different concepts, only opposite POLARITIES of one (deny here, allow
there), named differently because ste100 was written first. Both are term
lists now; see lint.py's TERM_LISTS and core/terms.py.
"""
from rulesets.slopwatch import lint
from core import checks as _checks, paths, terms as _terms

TERM_LISTS = lint.TERM_LISTS
CHECKS_TABLE = lint.CHECKS_TABLE

RULESET_ID = "slopwatch"
RULESET_NAME = "slopwatch"
CAPABILITIES = frozenset({"terms", "checks", "check_config"})

TRACKED_FILES = ["lint.py"]


def lint_and_gate(text, *, context=None, file_path=None):
    return lint.lint_and_gate(text, context=context, file_path=file_path)


def blocking_semantic_flags(semantic_flags):
    return lint.blocking_semantic_flags(semantic_flags)


def apply_mechanical_fixes(text, file_path=None):
    return lint.apply_mechanical_fixes(text, file_path=file_path)


def stats():
    # Derived, not a hand-maintained sentence -- the count in this string
    # drifted the moment terminology arrived, exactly the class of "second
    # copy of a fact" this codebase keeps deleting.
    return {"checks": f"{len(lint.ALL_CHECK_IDS)} "
                       f"({', '.join(sorted(lint.ALL_CHECK_IDS))})"}


def list_checks():
    return _checks.list_checks(lint.CHECKS_TABLE, paths.find_project_root(__file__), RULESET_ID)


def set_enabled_checks(check_ids):
    _checks.set_enabled_checks(lint.CHECKS_TABLE, paths.find_project_root(__file__),
                                RULESET_ID, check_ids)


def set_checks_enabled(states):
    _checks.set_checks_enabled(lint.CHECKS_TABLE, paths.find_project_root(__file__),
                                RULESET_ID, states)


def list_check_config():
    return _checks.list_check_config(lint.CHECKS_TABLE, paths.find_project_root(__file__), RULESET_ID)


def set_check_config(check_id, threshold=None, action=None):
    _checks.set_check_config(lint.CHECKS_TABLE, paths.find_project_root(__file__),
                              RULESET_ID, check_id, threshold=threshold, action=action)


def list_term_lists(file_path=None):
    """Every term list this ruleset owns, with its polarity and per-layer
    counts -- the modularity surface the dashboard's Vocabulary tab and
    `stopslop.py terms` both read. Identical shape across all three
    rulesets now, which is the whole point of core/terms.py."""
    return _terms.list_term_lists(RULESET_ID, TERM_LISTS,
                                   paths.find_project_root(__file__),
                                   file_path=file_path)


def add_term(list_id, term, note="", force=False):
    """Add one term to a list's project layer. No validator: these lists
    have no external standard to check a word against, so `force` is
    accepted (for one uniform signature across rulesets) and unused."""
    return _terms.add_term(RULESET_ID, TERM_LISTS,
                            paths.find_project_root(__file__),
                            list_id, term, note=note, force=force)


def remove_term(list_id, term):
    return _terms.remove_term(RULESET_ID, TERM_LISTS,
                               paths.find_project_root(__file__), list_id, term)
