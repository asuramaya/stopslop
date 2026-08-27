"""Whole custom rulesets: a project scaffolds a brand-new ruleset --
empty CHECKS_TABLE/TERM_LISTS -- without touching this tool's own
source, then fills it in with Phase 2/3's own "add list"/"add check" UI.
The same "content lives outside src/, discovery reads it back in" shape
as core/glossary_packs.py's custom packs, core/config.py's custom term
lists, and core/custom_checks.py's custom checks.

A custom ruleset is a real package at
<project_root>/.claude/stopslop/custom_rulesets/<ruleset_id>/__init__.py.
Unlike a custom CHECK's matcher body, nothing here is a project author's
own code -- `render_source` fully controls the generated file's content
(only `ruleset_id` and `name` are user-supplied, both validated before
they ever reach the template), so this module carries none of
core/custom_checks.py's validate-then-write-from-a-temp-path ceremony.
The generated module still satisfies the SAME contract
(rulesets.REQUIRED_ATTRS/CAPABILITY_ATTRS) a hand-written ruleset would
-- see rulesets/__init__.py, which does the actual contract enforcement
at registration time. This module only owns the FILE-LEVEL concerns
(paths, the template, a generic loader-by-path) so it never needs to
import the `rulesets` package itself -- rulesets/__init__.py imports
THIS module to discover custom rulesets, and importing it back here
would be a cycle.
"""
import importlib.machinery
import importlib.util
import os
import re
import shutil

_RULESET_ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")


class InvalidCustomRulesetError(Exception):
    """A custom ruleset's id/name failed validation, or its generated
    file failed to import -- the latter would be this module's own
    template bug, not a project author's mistake, since nothing here is
    project-authored code."""


def _custom_rulesets_dir(project_root):
    return os.path.join(project_root, ".claude", "stopslop", "custom_rulesets")


def _ruleset_dir(project_root, ruleset_id):
    return os.path.join(_custom_rulesets_dir(project_root), ruleset_id)


def _init_path(project_root, ruleset_id):
    return os.path.join(_ruleset_dir(project_root, ruleset_id), "__init__.py")


def custom_ruleset_ids(project_root):
    d = _custom_rulesets_dir(project_root)
    if not os.path.isdir(d):
        return []
    return sorted(name for name in os.listdir(d)
                  if os.path.isfile(os.path.join(d, name, "__init__.py")))


def load_ruleset_module(project_root, ruleset_id):
    """Import <ruleset_id>/__init__.py by path, as rulesets/__init__.py's
    own discovery does for a built-in subpackage via pkgutil -- except a
    custom ruleset isn't physically under rulesets/'s own __path__, so it
    can't go through the normal package-import machinery at all. An
    explicit SourceFileLoader, not a bare path, for the same reason
    core.custom_checks._load_one needs one: a loader inferred purely from
    the file's own extension is the common case, but this module refuses
    to depend on that inference holding for every caller forever."""
    path = _init_path(project_root, ruleset_id)
    name = f"_stopslop_custom_ruleset_{ruleset_id}"
    loader = importlib.machinery.SourceFileLoader(name, path)
    spec = importlib.util.spec_from_file_location(name, path, loader=loader)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as e:
        raise InvalidCustomRulesetError(
            f"custom_rulesets/{ruleset_id}/__init__.py failed to import: {e}") from e
    return module


_TEMPLATE = '''"""Scaffolded ruleset {ruleset_id!r} ({name!r}) -- added via the
dashboard. Starts with no checks and no term lists of its own; add them
from the Checks and Vocabulary pages, or hand-edit this file directly --
it is a real, ordinary ruleset module, not machine-only.
"""
from core import checks as _checks, config as _config, custom_checks as _custom_checks
from core import paths as _paths, terms as _terms
from core.blocks import HEADER_RE as _HEADER_RE, LIST_ITEM_RE as _LIST_ITEM_RE
from core.blocks import split_into_blocks, tokenize_sentences
import re as _re

RULESET_ID = {ruleset_id!r}
RULESET_NAME = {name!r}
CAPABILITIES = frozenset({{"terms", "checks", "check_config", "custom_checks"}})
TRACKED_FILES = ["__init__.py"]

# Starts empty on purpose -- a scaffolded ruleset has no vocabulary or
# checks of its own until a project adds them through the dashboard.
TERM_LISTS = {{}}
CHECKS_TABLE = {{}}

# Every check this ruleset's own CHECKS_TABLE could ever declare runs
# against a SENTENCE or the whole DOCUMENT -- see lint_and_gate below --
# so those are the only units a custom check may use here too.
CUSTOM_CHECK_UNITS = _custom_checks.DEFAULT_ALLOWED_UNITS


def effective_checks_table():
    try:
        project_root = _paths.find_project_root(__file__)
    except Exception:
        return CHECKS_TABLE
    return _custom_checks.effective_checks_table(CHECKS_TABLE, project_root, RULESET_ID,
                                                   CUSTOM_CHECK_UNITS)


def _effective_lists():
    return _config.effective_term_lists(TERM_LISTS, RULESET_ID, _paths.find_project_root(__file__))


def list_term_lists(file_path=None):
    return _terms.list_term_lists(RULESET_ID, _effective_lists(),
                                   _paths.find_project_root(__file__), file_path=file_path)


def add_term(list_id, term, note="", force=False):
    return _terms.add_term(RULESET_ID, _effective_lists(),
                            _paths.find_project_root(__file__), list_id, term,
                            note=note, force=force)


def remove_term(list_id, term):
    return _terms.remove_term(RULESET_ID, _effective_lists(),
                               _paths.find_project_root(__file__), list_id, term)


def list_checks():
    return _checks.list_checks(effective_checks_table(), _paths.find_project_root(__file__), RULESET_ID)


def set_enabled_checks(check_ids):
    _checks.set_enabled_checks(effective_checks_table(), _paths.find_project_root(__file__),
                                RULESET_ID, check_ids)


def set_checks_enabled(states):
    _checks.set_checks_enabled(effective_checks_table(), _paths.find_project_root(__file__),
                                RULESET_ID, states)


def list_check_config():
    return _checks.list_check_config(effective_checks_table(), _paths.find_project_root(__file__),
                                      RULESET_ID)


def set_check_config(check_id, threshold=None, action=None, **params):
    _checks.set_check_config(effective_checks_table(), _paths.find_project_root(__file__),
                              RULESET_ID, check_id, threshold=threshold, action=action, **params)


def custom_check_units():
    return sorted(u.value for u in CUSTOM_CHECK_UNITS)


def custom_check_ids():
    return _custom_checks.custom_check_ids(_paths.find_project_root(__file__), RULESET_ID)


def add_custom_check(check_id, unit, catches, instead, threshold, action, fn_body):
    _custom_checks.add_custom_check(_paths.find_project_root(__file__), RULESET_ID,
                                     set(CHECKS_TABLE), check_id, unit, catches, instead,
                                     threshold, action, fn_body, CUSTOM_CHECK_UNITS)


def update_custom_check(check_id, unit, catches, instead, threshold, action, fn_body):
    _custom_checks.update_custom_check(_paths.find_project_root(__file__), RULESET_ID,
                                        set(CHECKS_TABLE), check_id, unit, catches, instead,
                                        threshold, action, fn_body, CUSTOM_CHECK_UNITS)


def remove_custom_check(check_id):
    _custom_checks.remove_custom_check(_paths.find_project_root(__file__), RULESET_ID, check_id)


def _enabled_check_ids(file_path=None):
    table = effective_checks_table()
    try:
        project_root = _paths.find_project_root(__file__)
    except Exception:
        return set(_checks.all_check_ids(table))
    return _checks.enabled_check_ids(table, project_root, RULESET_ID, file_path)


def lint_and_gate(text, *, context=None, file_path=None):
    """Block-aware the same way every hand-written ruleset's own
    lint_and_gate is (core.blocks.split_into_blocks): code fences are
    never linted, each header/list-item/paragraph is sentence-tokenized
    within its own bounds. Every check this ruleset ever runs -- built-in
    (none, today) or custom (SENTENCE/DOCUMENT only) -- reads one of the
    two domains built here."""
    sentences = []
    for block_type, content in split_into_blocks(text):
        if block_type in ("fence", "blank"):
            continue
        elif block_type == "header":
            block_text = _HEADER_RE.sub("", content).strip()
        elif block_type == "list_item":
            m = _LIST_ITEM_RE.match(content)
            block_text = m.group(2) if m else content
        else:
            block_text = content
        block_text = _re.sub(r"`[^`\\n]+`", " ", block_text)
        sentences.extend(tokenize_sentences(block_text))

    mechanical, semantic = _checks.run_checks(
        effective_checks_table(), sentences=sentences, text=" ".join(sentences))

    enabled = _enabled_check_ids(file_path)
    mechanical = [f for f in mechanical if f["kind"] in enabled]
    semantic = [f for f in semantic if f["kind"] in enabled]

    status = "clean" if not mechanical and not semantic else (
        "semantic_flags" if semantic else "mechanical_violations")
    return {{
        "status": status,
        "sentence_count": len(sentences),
        "mechanical_violations": mechanical,
        "semantic_flags": semantic,
    }}


def blocking_semantic_flags(semantic_flags):
    project_root = _paths.find_project_root(__file__)
    return _checks.blocking_semantic_flags(effective_checks_table(), project_root,
                                            RULESET_ID, semantic_flags)


def apply_mechanical_fixes(text, file_path=None):
    # No built-in check ships a mechanical fix here -- a scaffolded
    # ruleset starts with none, and a custom check (see core.checks.Check
    # .classify) is flag-only by default. Real if a project ever adds a
    # mechanical-classified custom check: this stays a documented,
    # deliberate no-op until then, not a silent gap nobody chose.
    return text
'''


def render_source(ruleset_id, name):
    return _TEMPLATE.format(ruleset_id=ruleset_id, name=name)


def scaffold_ruleset(project_root, ruleset_id, name, existing_ids):
    """Write a new custom ruleset package. Refuses an id that isn't
    lowercase/snake_case, one colliding with any currently-known ruleset
    (built-in or already-scaffolded custom -- `existing_ids` is the
    caller's own full picture, not just this module's), or one whose
    DIRECTORY already exists on disk even though it ISN'T in
    `existing_ids` -- a leftover from an interrupted previous scaffold,
    or two concurrent submissions racing each other. That last case
    raises ValueError too, the same as the ordinary collision above,
    rather than a raw FileExistsError from os.makedirs escaping as a
    500 -- every other refusal in this module is already a clean,
    caller-facing exception; this one was the exception to that, found
    live via the dashboard's own error-banner pattern never firing for
    it. Validates by importing the freshly-written file before
    returning -- a template bug (there should never be one; this is
    regression insurance, not a project-author safety net) removes the
    whole directory rather than leaving a broken package registration
    would stumble over later."""
    ruleset_id = ruleset_id.strip()
    if not _RULESET_ID_RE.match(ruleset_id):
        raise InvalidCustomRulesetError(
            f"ruleset id {ruleset_id!r} must start with a lowercase letter and contain only "
            f"lowercase letters, digits, underscores")
    if ruleset_id in existing_ids:
        raise ValueError(f"a ruleset {ruleset_id!r} already exists -- choose a different id")
    name = name.strip() or ruleset_id
    ruleset_dir = _ruleset_dir(project_root, ruleset_id)
    try:
        os.makedirs(ruleset_dir, exist_ok=False)
    except FileExistsError:
        raise ValueError(
            f"a ruleset {ruleset_id!r} already exists -- choose a different id") from None
    try:
        with open(_init_path(project_root, ruleset_id), "w") as f:
            f.write(render_source(ruleset_id, name))
        load_ruleset_module(project_root, ruleset_id)  # raises on a bad template
    except Exception:
        shutil.rmtree(ruleset_dir, ignore_errors=True)
        raise


def remove_ruleset(project_root, ruleset_id):
    """Delete one custom ruleset's whole package directory. The caller
    (rulesets.unregister_ruleset, and the webui route before that) is
    responsible for checking no routing rule still references this id --
    this function only ever touches the filesystem."""
    shutil.rmtree(_ruleset_dir(project_root, ruleset_id), ignore_errors=True)
