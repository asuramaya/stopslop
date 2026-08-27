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
from core import checks as _checks, config as _config, custom_checks as _custom_checks, paths, terms as _terms

TERM_LISTS = lint.TERM_LISTS
CHECKS_TABLE = lint.CHECKS_TABLE

RULESET_ID = "codewatch"
RULESET_NAME = "codewatch"
CAPABILITIES = frozenset({"terms", "checks", "check_config", "custom_checks"})

TRACKED_FILES = ["lint.py"]


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
    return _checks.list_checks(lint.effective_checks_table(), paths.find_project_root(__file__), RULESET_ID)


def set_enabled_checks(check_ids):
    _checks.set_enabled_checks(lint.effective_checks_table(), paths.find_project_root(__file__),
                                RULESET_ID, check_ids)


def set_checks_enabled(states):
    _checks.set_checks_enabled(lint.effective_checks_table(), paths.find_project_root(__file__),
                                RULESET_ID, states)


def list_check_config():
    return _checks.list_check_config(lint.effective_checks_table(), paths.find_project_root(__file__), RULESET_ID)


def set_check_config(check_id, threshold=None, action=None):
    _checks.set_check_config(lint.effective_checks_table(), paths.find_project_root(__file__),
                              RULESET_ID, check_id, threshold=threshold, action=action)


def custom_check_units():
    return sorted(u.value for u in lint.CUSTOM_CHECK_UNITS)


def custom_check_ids():
    return _custom_checks.custom_check_ids(paths.find_project_root(__file__), RULESET_ID)


def add_custom_check(check_id, unit, catches, instead, threshold, action, fn_body):
    _custom_checks.add_custom_check(paths.find_project_root(__file__), RULESET_ID,
                                     set(lint.CHECKS_TABLE), check_id, unit, catches, instead,
                                     threshold, action, fn_body, lint.CUSTOM_CHECK_UNITS)


def update_custom_check(check_id, unit, catches, instead, threshold, action, fn_body):
    _custom_checks.update_custom_check(paths.find_project_root(__file__), RULESET_ID,
                                        set(lint.CHECKS_TABLE), check_id, unit, catches, instead,
                                        threshold, action, fn_body, lint.CUSTOM_CHECK_UNITS)


def remove_custom_check(check_id):
    _custom_checks.remove_custom_check(paths.find_project_root(__file__), RULESET_ID, check_id)


def _effective_lists():
    """TERM_LISTS plus this project's own custom_term_lists declarations
    for codewatch -- see core.config.effective_term_lists. Resolved fresh
    per call (never cached), same posture as every other project-config
    read here."""
    return _config.effective_term_lists(TERM_LISTS, RULESET_ID, paths.find_project_root(__file__))


def list_term_lists(file_path=None):
    """See rulesets/slopwatch/__init__.py's list_term_lists() -- identical
    shape and identical delegation, just codewatch's one list."""
    return _terms.list_term_lists(RULESET_ID, _effective_lists(),
                                   paths.find_project_root(__file__),
                                   file_path=file_path)


def add_term(list_id, term, note="", force=False):
    return _terms.add_term(RULESET_ID, _effective_lists(),
                            paths.find_project_root(__file__),
                            list_id, term, note=note, force=force)


def remove_term(list_id, term):
    return _terms.remove_term(RULESET_ID, _effective_lists(),
                               paths.find_project_root(__file__), list_id, term)
