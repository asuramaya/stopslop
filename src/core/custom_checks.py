"""Per-ruleset custom checks: real Python matcher functions a project adds
without editing this tool's own source, the same "content lives outside
src/, discovery reads it back in" shape as core/glossary_packs.py's custom
packs and core/config.py's custom term lists.

A custom check is a real file at
<project_root>/.claude/stopslop/custom_checks/<ruleset_id>/<check_id>.py,
generated from the dashboard's Checks page "Add check" form (id, catches,
instead, unit, default threshold/action, and the matcher's own body) but
never a sandboxed subset -- this is not a new execution surface. Anyone
with write access to this repo already has arbitrary code execution via
the hook mechanism itself (pretool_hook.py imports and runs every
ruleset's own Python on every gate call); see the architecture plan's "on
full custom-code checks and safety" note. The file is real, inspectable,
editable by hand, and portable -- exactly as legitimate a check as a
shipped one, just not one this tool's own source declares.

Which Unit values a ruleset accepts from a custom check is declared by
THAT RULESET (its own `allowed_units`, e.g. rulesets/slopwatch/lint.py's
CUSTOM_CHECK_UNITS), not fixed here -- because what a unit even MEANS is
ruleset-specific past a certain point. SENTENCE/DOCUMENT are safe for
every prose ruleset (the full tokenized-sentence list and the whole
assembled lintable text are built identically everywhere), and codewatch
additionally allows LINE, because codewatch's own "lines" domain really
is every line of the file with no special scoping -- unlike slopwatch's
LINE domain, which is list-item lines ONLY, not every line. A custom
check declaring a unit its own ruleset doesn't allow is rejected loudly
at load time, the same "fails at load time, not deep inside a live gate
decision" posture rulesets/__init__.py's own _register() already takes
for a malformed ruleset.
"""
import importlib.machinery
import importlib.util
import inspect
import os
import re
import textwrap

from core import checks as _checks

DEFAULT_ALLOWED_UNITS = frozenset({_checks.Unit.SENTENCE, _checks.Unit.DOCUMENT})
_CHECK_ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")


class InvalidCustomCheckError(Exception):
    """A custom check file exists but doesn't satisfy the contract, or a
    submitted one would not."""


def _custom_checks_dir(project_root):
    return os.path.join(project_root, ".claude", "stopslop", "custom_checks")


def _ruleset_dir(project_root, ruleset_id):
    return os.path.join(_custom_checks_dir(project_root), ruleset_id)


def _check_path(project_root, ruleset_id, check_id):
    return os.path.join(_ruleset_dir(project_root, ruleset_id), f"{check_id}.py")


def custom_check_ids(project_root, ruleset_id):
    d = _ruleset_dir(project_root, ruleset_id)
    if not os.path.isdir(d):
        return []
    return sorted(name[:-len(".py")] for name in os.listdir(d) if name.endswith(".py"))


def _load_one(path, ruleset_id, check_id, allowed_units):
    # An explicit SourceFileLoader, not a bare path -- validation loads
    # from a TEMP path ending in ".py.tmp" (see _write_validated), and
    # spec_from_file_location's own extension-sniffing returns None (not
    # a real Python-source spec) for a suffix it doesn't recognize.
    name = f"_stopslop_custom_check_{ruleset_id}_{check_id}"
    loader = importlib.machinery.SourceFileLoader(name, path)
    spec = importlib.util.spec_from_file_location(name, path, loader=loader)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as e:
        raise InvalidCustomCheckError(
            f"custom_checks/{ruleset_id}/{check_id}.py failed to import: {e}") from e
    check = getattr(module, "CHECK", None)
    if not isinstance(check, _checks.Check):
        raise InvalidCustomCheckError(
            f"custom_checks/{ruleset_id}/{check_id}.py has no CHECK (a core.checks.Check)")
    if check.id != check_id:
        raise InvalidCustomCheckError(
            f"custom_checks/{ruleset_id}/{check_id}.py's CHECK.id is {check.id!r}, "
            f"expected {check_id!r} (must match its own filename)")
    if check.unit not in allowed_units:
        raise InvalidCustomCheckError(
            f"custom_checks/{ruleset_id}/{check_id}.py declares unit {check.unit.value!r} -- "
            f"the {ruleset_id!r} ruleset only allows {sorted(u.value for u in allowed_units)} "
            f"for a custom check")
    if check.classify != "semantic":
        # apply_mechanical_fixes is a fixed, hand-written function per
        # ruleset (not data-driven off CHECKS_TABLE) -- it has no way to
        # know about, or apply, a custom check's own fix. A custom check
        # classified "mechanical" (the template never generates this;
        # only a hand-edit can) would land in mechanical_violations, and
        # the live gate reports "auto-fixed" and ALLOWS the write while
        # the actual violation goes through completely untouched. Refused
        # here, at load time, rather than silently shipping that gap --
        # the same "fails loudly, not deep inside a live gate decision"
        # posture this whole module already takes for every other
        # malformed field.
        raise InvalidCustomCheckError(
            f"custom_checks/{ruleset_id}/{check_id}.py declares "
            f"classify={check.classify!r} -- a custom check must stay "
            f"classify='semantic' (the default; leave CHECK's classify "
            f"argument out entirely). Nothing here can auto-fix a custom "
            f"check's own violation, so 'mechanical' would let a flagged "
            f"write through unfixed.")
    return check


def load_custom_checks(project_root, ruleset_id, built_in_ids, allowed_units=DEFAULT_ALLOWED_UNITS):
    """{check_id: Check} for this ruleset's custom checks, or {} if none
    exist. Raises InvalidCustomCheckError loudly for a syntax error, a
    missing/malformed CHECK, a unit this ruleset doesn't allow, or a
    check id colliding with a BUILT-IN one -- a custom check can never
    silently shadow or replace a shipped check; disable the built-in via
    stopslop.config.json instead."""
    ids = custom_check_ids(project_root, ruleset_id)
    out = {}
    for check_id in ids:
        if check_id in built_in_ids:
            raise InvalidCustomCheckError(
                f"custom_checks/{ruleset_id}/{check_id}.py: {check_id!r} "
                f"collides with a built-in check")
        out[check_id] = _load_one(_check_path(project_root, ruleset_id, check_id),
                                   ruleset_id, check_id, allowed_units)
    return out


def effective_checks_table(built_in_table, project_root, ruleset_id, allowed_units=DEFAULT_ALLOWED_UNITS):
    """built_in_table merged with this ruleset's custom checks -- built-in
    always wins on an id collision (load_custom_checks already refuses to
    load a colliding id; this is belt-and-suspenders, the same posture
    core.terms.py's/core.config.py's own merge functions take). Any load
    failure propagates -- never silently drops a project's custom check
    from the live gate without saying why, the same "fails loudly" stance
    every other layer here takes."""
    custom = load_custom_checks(project_root, ruleset_id, set(built_in_table), allowed_units)
    merged = dict(built_in_table)
    for check_id, check in custom.items():
        merged.setdefault(check_id, check)
    return merged


def extra_by_check_for_custom(project_root, ruleset_id, custom_check_ids, effective_lists, file_path=None):
    """{check_id: [word, ...]} for every CUSTOM check bound to a term
    list, in the same list-declares-the-check-it-feeds direction a
    built-in check's own TERM_LISTS entry already uses (core/terms.py's
    own note explains why the binding lives on the list, not the check)
    -- a custom check reads a curated Vocabulary list exactly the way a
    shipped one does, via its generated function's own `extra=()`
    parameter, with no new mechanism of its own. Only ever produces
    entries for ids in `custom_check_ids`, so merging this dict into a
    ruleset's own hand-written extra_by_check can never override or
    shadow a built-in check's entry -- a built-in list's `feeds` always
    names a built-in check id, never a custom one, because the webui
    only ever offers a CUSTOM list as a bindable target in the first
    place (a built-in list's spec lives in read-only Python source)."""
    from core import terms as _terms
    out = {}
    for list_id, spec in effective_lists.items():
        check_id = spec.get("feeds")
        if check_id in custom_check_ids:
            layers = _terms.resolve(spec, project_root, ruleset_id, list_id, file_path=file_path)
            out[check_id] = sorted(layers["effective"])
    return out


def get_custom_check_fields(project_root, ruleset_id, check_id, allowed_units=DEFAULT_ALLOWED_UNITS):
    """The dashboard's "Add a check" form has no counterpart for viewing
    or editing a check already saved -- once written, the matcher body a
    project author typed is invisible again unless they open the file on
    disk by hand. This reconstructs exactly what that form would have
    been filled in with, so an "Edit" affordance can prefill it: every
    metadata field comes straight off the loaded CHECK object, and the
    matcher body comes from `inspect.getsource` on the loaded function
    (not a second hand-parse of the file's own template markers) with its
    `def check_<id>(...):` line dropped and the rest dedented back to
    what render_source() originally indented -- render_source's own
    indent-every-line step is exactly textwrap.dedent's inverse, so this
    round-trips the author's original text byte for byte, blank lines
    included."""
    path = _check_path(project_root, ruleset_id, check_id)
    if not os.path.exists(path):
        raise ValueError(f"no custom check {check_id!r} to inspect -- add it first")
    check = _load_one(path, ruleset_id, check_id, allowed_units)
    body_lines = inspect.getsource(check.fn).splitlines()[1:]
    fn_body = textwrap.dedent("\n".join(body_lines)).strip("\n")
    return {
        "id": check.id, "unit": check.unit.value, "catches": check.catches,
        "instead": check.instead, "threshold": check.default_threshold,
        "action": check.default_action, "fn_body": fn_body,
        "terms_list": check.terms_list,
    }


_TEMPLATE = '''"""Custom check {check_id!r} for the {ruleset_id!r} ruleset --
added via the dashboard's Checks page. Not machine-only: this is a real
Python file, safe to hand-edit, safe to move, safe to remove outright."""
from core.checks import Check, Unit


def check_{check_id}({arg}, extra=()):
{body}


CHECK = Check(
    id={check_id!r}, unit=Unit.{unit_name}, fn=check_{check_id},
    catches={catches!r}, instead={instead!r},
    default_threshold={threshold!r}, default_action={action!r},{terms_list_kwarg}
)
'''


_UNIT_ARG_NAMES = {
    _checks.Unit.SENTENCE: "sentence",
    _checks.Unit.DOCUMENT: "text",
    _checks.Unit.LINE: "line",
}


def render_source(ruleset_id, check_id, unit, catches, instead, threshold, action, fn_body,
                   terms_list=None):
    """The full custom-check file's source text for one check, built from
    the dashboard form's own fields -- never asks a project author to
    hand-write the Check(...) construction correctly, only the matcher
    body itself. `fn_body` is the untouched textarea contents, indented
    under a generated function signature; a project author's own
    docstrings/comments/blank lines inside it survive exactly as typed.

    The generated function always takes a trailing `extra=()` -- whether
    or not `terms_list` binds one now, so binding or unbinding one later
    (via update_custom_check) never has to touch a signature the fn_body
    author already wrote against. `terms_list`, when given, is the id of
    a term list THIS ruleset already declares (built-in or custom) whose
    own `feeds` names this check -- see
    core.custom_checks.extra_by_check_for_custom for the resolving side;
    this function only ever records the pointer onto the CHECK object."""
    unit = _checks.Unit(unit)
    arg = _UNIT_ARG_NAMES.get(unit, "item")
    lines = fn_body.rstrip("\n").split("\n") or [""]
    body = "\n".join("    " + line if line.strip() else "" for line in lines) or "    return []"
    terms_list_kwarg = f"\n    terms_list={terms_list!r}," if terms_list else ""
    return _TEMPLATE.format(
        check_id=check_id, ruleset_id=ruleset_id, arg=arg, body=body,
        unit_name=unit.name, catches=catches, instead=instead,
        threshold=threshold, action=action, terms_list_kwarg=terms_list_kwarg,
    )


def add_custom_check(project_root, ruleset_id, built_in_ids, check_id,
                      unit, catches, instead, threshold, action, fn_body,
                      allowed_units=DEFAULT_ALLOWED_UNITS, terms_list=None):
    """Validate-then-write: renders the file, imports it from a TEMP path
    first, and only copies it into place if that import succeeds and the
    resulting CHECK passes every check load_custom_checks itself would
    apply -- a syntax error or a bad unit never overwrites a working
    file, and never leaves a half-written one behind either. Refuses an
    id colliding with a built-in or an existing custom check outright
    (this is ADD, not upsert; use update_custom_check to replace one)."""
    check_id = check_id.strip()
    if not _CHECK_ID_RE.match(check_id):
        raise InvalidCustomCheckError(
            f"check id {check_id!r} must start with a lowercase letter and contain only "
            f"lowercase letters, digits, underscores")
    if check_id in built_in_ids:
        raise ValueError(f"{check_id!r} is a built-in check id -- choose a different name")
    if check_id in custom_check_ids(project_root, ruleset_id):
        raise ValueError(f"a custom check {check_id!r} already exists -- remove it first to replace it")
    _write_validated(project_root, ruleset_id, built_in_ids, check_id,
                      unit, catches, instead, threshold, action, fn_body, allowed_units, terms_list)


def update_custom_check(project_root, ruleset_id, built_in_ids, check_id,
                         unit, catches, instead, threshold, action, fn_body,
                         allowed_units=DEFAULT_ALLOWED_UNITS, terms_list=None):
    """Same validate-then-write discipline as add_custom_check, but for
    an EXISTING custom check -- the id must already exist as a custom
    check (never a built-in; those have no file here to update)."""
    if check_id not in custom_check_ids(project_root, ruleset_id):
        raise ValueError(f"no custom check {check_id!r} to update -- add it first")
    _write_validated(project_root, ruleset_id, built_in_ids, check_id,
                      unit, catches, instead, threshold, action, fn_body, allowed_units, terms_list)


def _write_validated(project_root, ruleset_id, built_in_ids, check_id,
                      unit, catches, instead, threshold, action, fn_body, allowed_units,
                      terms_list=None):
    try:
        unit_enum = _checks.Unit(unit)
    except ValueError:
        raise InvalidCustomCheckError(
            f"unit must be one of {sorted(u.value for u in allowed_units)}, got {unit!r}")
    if unit_enum not in allowed_units:
        raise InvalidCustomCheckError(
            f"the {ruleset_id!r} ruleset only allows "
            f"{sorted(u.value for u in allowed_units)} for a custom check, got {unit!r}")
    source = render_source(ruleset_id, check_id, unit, catches, instead, threshold, action, fn_body,
                            terms_list=terms_list)

    ruleset_dir = _ruleset_dir(project_root, ruleset_id)
    os.makedirs(ruleset_dir, exist_ok=True)
    tmp_path = _check_path(project_root, ruleset_id, check_id) + ".tmp"
    with open(tmp_path, "w") as f:
        f.write(source)
    try:
        check = _load_one(tmp_path, ruleset_id, check_id, allowed_units)
        if check_id in built_in_ids:
            raise InvalidCustomCheckError(f"{check_id!r} collides with a built-in check")
    except Exception:
        os.remove(tmp_path)
        raise
    os.replace(tmp_path, _check_path(project_root, ruleset_id, check_id))


def remove_custom_check(project_root, ruleset_id, check_id):
    """Delete one custom check's file. A no-op (not an error) if it's
    already gone -- matches remove_pack's/remove_term's own idempotent
    posture for a repeated or racing removal."""
    path = _check_path(project_root, ruleset_id, check_id)
    if os.path.exists(path):
        os.remove(path)
