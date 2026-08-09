"""Contract surface for the codewatch ruleset -- see lint.py for the actual
checks and the module docstring there for why this ruleset exists (proving
stopslop's plugin contract generalizes past prose into code).

CAPABILITIES has no "word_lookup", the same reason slopwatch's doesn't: no
external standard to look a single word up against. It does have "terms" --
generic_naming is "match against a list of denylisted name stems", the same
shared term-list shape (core/terms.py) slopwatch's five checks and ste100's
project vocabulary all use now. See lint.py's TERM_LISTS, including the
note there on the ALLOW list this ruleset should eventually have and
structurally could not have had before.
"""
from rulesets.codewatch import lint
from core import config as _core_config, paths, terms as _terms

TERM_LISTS = lint.TERM_LISTS

RULESET_ID = "codewatch"
RULESET_NAME = "codewatch"
CAPABILITIES = frozenset({"terms", "checks", "check_config"})

TRACKED_FILES = ["lint.py"]

# (catches, instead) -- see rulesets/slopwatch/__init__.py's CHECKS for why
# this is two fields rather than one prewritten sentence.
CHECKS = {
    "trivial_comment": ("Comments that only restate the next line",
                        "cut them, or say why instead"),
    "narrative_comment": ("Separator bars, \"Phase/Step N\" headers, "
                          "step-by-step narration",
                          "the code already says what it does"),
    "meta_comment": ("Comments citing the plan/spec/ticket, or narrating "
                     "before/after state",
                     "that belongs in a commit message, not the source"),
    "swallowed_exception": ("Bare except-then-pass",
                            "log the error, re-raise it, or name why it is "
                            "safe to ignore"),
    "mutable_default_arg": ("Mutable default arguments: def f(x=[])",
                            "they are shared across every call; use None and "
                            "build the real default inside the function"),
    "print_debug": ("Leftover print() calls",
                    "use logging, or remove them before this ships"),
    "todo_stub": ("TODO/FIXME/HACK comments with no tracking issue",
                  "link an issue, or resolve it now"),
    "generic_naming": ("Generic, numbered names: helper_1, data2, temp1",
                       "say what the value actually is"),
    "tautological_assert": ("assert True",
                            "it can never fail; assert the real condition, "
                            "or remove it"),
    "constant_condition": ("if True: / if False:",
                           "a dead branch, or leftover debug code"),
}


def lint_and_gate(text, *, context=None, file_path=None):
    return lint.lint_and_gate(text, context=context, file_path=file_path)


def blocking_semantic_flags(semantic_flags):
    return lint.blocking_semantic_flags(semantic_flags)


def apply_mechanical_fixes(text, file_path=None):
    return lint.apply_mechanical_fixes(text, file_path=file_path)


def stats():
    return {"checks": "10 (trivial_comment, narrative_comment, meta_comment, "
                       "swallowed_exception, mutable_default_arg, print_debug, "
                       "todo_stub, generic_naming, tautological_assert, "
                       "constant_condition)"}


def list_checks():
    """See rulesets/slopwatch/__init__.py's list_checks() -- identical
    shape and rationale, just against codewatch's own 10 checks."""
    project_root = paths.find_project_root(__file__)
    disabled = set(_core_config.disabled_checks(project_root, RULESET_ID))
    return {
        check_id: {"catches": CHECKS.get(check_id, ("", ""))[0],
                   "instead": CHECKS.get(check_id, ("", ""))[1],
                   "enabled": check_id not in disabled}
        for check_id in sorted(lint.ALL_CHECK_IDS)
    }


def set_enabled_checks(check_ids):
    unknown = set(check_ids) - lint.ALL_CHECK_IDS
    if unknown:
        raise ValueError(f"unknown check id(s): {sorted(unknown)} -- "
                          f"known: {sorted(lint.ALL_CHECK_IDS)}")
    disabled = sorted(lint.ALL_CHECK_IDS - set(check_ids))
    project_root = paths.find_project_root(__file__)
    _core_config.save_disabled_checks(project_root, RULESET_ID, disabled)


def set_checks_enabled(states):
    """Turn the named checks on or off, leaving every other check alone --
    {check_id: bool}. Merge semantics, the same shape set_check_config has, and
    the counterpart to set_enabled_checks's replace semantics: see
    core.config.merge_disabled_checks for which callers need which, and for
    the silent-mass-disable bug that made the distinction worth a second
    method rather than a comment."""
    unknown = set(states) - lint.ALL_CHECK_IDS
    if unknown:
        raise ValueError(f"unknown check id(s): {sorted(unknown)} -- "
                          f"known: {sorted(lint.ALL_CHECK_IDS)}")
    project_root = paths.find_project_root(__file__)
    _core_config.merge_disabled_checks(project_root, RULESET_ID, states)


def list_check_config():
    """See rulesets/slopwatch/__init__.py's list_check_config() --
    identical shape, just against codewatch's own 10 checks."""
    current = lint._check_config()
    return {check_id: {"threshold": spec["threshold"], "action": spec["action"],
                        "default_threshold": lint.DEFAULT_CHECK_CONFIG[check_id]["threshold"],
                        "default_action": lint.DEFAULT_CHECK_CONFIG[check_id]["action"]}
            for check_id, spec in current.items()}


def set_check_config(check_id, threshold=None, action=None):
    """See rulesets/slopwatch/__init__.py's set_check_config() --
    identical merge-not-replace semantics and validation."""
    if check_id not in lint.ALL_CHECK_IDS:
        raise ValueError(f"unknown check id {check_id!r} -- "
                          f"known: {sorted(lint.ALL_CHECK_IDS)}")
    if threshold is not None and (not isinstance(threshold, int)
                                   or isinstance(threshold, bool) or threshold < 1):
        raise ValueError(f"threshold must be a whole number >= 1, got {threshold!r}")
    if action is not None and action not in ("block", "warn"):
        raise ValueError(f"action must be 'block' or 'warn', got {action!r}")
    project_root = paths.find_project_root(__file__)
    spec = dict(_core_config.check_config(project_root, RULESET_ID).get(check_id, {}))
    if threshold is not None:
        spec["threshold"] = threshold
    if action is not None:
        spec["action"] = action
    _core_config.save_check_config(project_root, RULESET_ID, check_id, spec)


def list_term_lists(file_path=None):
    """See rulesets/slopwatch/__init__.py's list_term_lists() -- identical
    shape and identical delegation, just codewatch's one list."""
    return _terms.list_term_lists(RULESET_ID, TERM_LISTS,
                                   paths.find_project_root(__file__),
                                   file_path=file_path)


def add_term(list_id, term, note="", force=False):
    return _terms.add_term(RULESET_ID, TERM_LISTS,
                            paths.find_project_root(__file__),
                            list_id, term, note=note, force=force)


def remove_term(list_id, term):
    return _terms.remove_term(RULESET_ID, TERM_LISTS,
                               paths.find_project_root(__file__), list_id, term)
