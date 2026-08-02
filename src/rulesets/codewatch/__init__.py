"""Contract surface for the codewatch ruleset -- see lint.py for the actual
checks and the module docstring there for why this ruleset exists (proving
stopslop's plugin contract generalizes past prose into code).

CAPABILITIES is deliberately empty, the same reason slopwatch's is: no
closed vocabulary, no glossary concept.
"""
from rulesets.codewatch import lint

RULESET_ID = "codewatch"
RULESET_NAME = "codewatch"
CAPABILITIES = frozenset()

TRACKED_FILES = ["lint.py"]

PRINCIPLE_TEXT = {
    "trivial_comment": "Comments that only restate the next line keep showing "
                       "up -- cut them, or say why instead.",
    "narrative_comment": "Decorative separators, \"Phase/Step N\" headers, and "
                       "step-by-step narration keep showing up in code comments "
                       "-- the code already says what it does.",
    "meta_comment": "Comments referencing the plan/spec/ticket, or narrating "
                       "before/after state, keep showing up -- that belongs in "
                       "a commit message, not the source.",
    "swallowed_exception": "Bare except-then-pass keeps showing up -- log the "
                       "error, re-raise it, or name why it's safe to ignore.",
    "mutable_default_arg": "Mutable default arguments (def f(x=[])) keep "
                       "showing up -- they're shared across every call; use "
                       "None and build the real default inside the function.",
    "print_debug": "Leftover print() calls keep showing up -- use logging, "
                       "or remove them before this ships.",
    "todo_stub": "Untracked TODO/FIXME/HACK comments keep showing up -- link "
                       "a tracking issue, or resolve it now.",
    "generic_naming": "Generic, numbered names (helper_1, data2, temp1) keep "
                       "showing up -- say what the value actually is.",
    "tautological_assert": "assert True keeps showing up -- it can never "
                       "fail; assert the real condition, or remove it.",
    "constant_condition": "if True: / if False: keeps showing up -- a dead "
                       "branch, or leftover debug code.",
}


def lint_and_gate(text, *, context=None):
    return lint.lint_and_gate(text, context=context)


def blocking_semantic_flags(semantic_flags):
    return lint.blocking_semantic_flags(semantic_flags)


def apply_mechanical_fixes(text):
    return lint.apply_mechanical_fixes(text)


def stats():
    return {"checks": "10 (trivial_comment, narrative_comment, meta_comment, "
                       "swallowed_exception, mutable_default_arg, print_debug, "
                       "todo_stub, generic_naming, tautological_assert, "
                       "constant_condition)"}
