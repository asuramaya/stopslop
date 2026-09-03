"""Shared scaffolding for a ruleset's per-check configuration.

Before this module, every ruleset's `lint.py` hand-rolled its own
`ALL_CHECK_IDS`, `DEFAULT_CHECK_CONFIG`, `_check_config()` and
`_enabled_check_ids()`, and every ruleset's `__init__.py` hand-rolled its
own `list_checks`/`set_enabled_checks`/`set_checks_enabled`/
`list_check_config`/`set_check_config` -- near-verbatim copies of each
other (the source comments used to say "see slopwatch's own docstring,
identical shape"), with one real behavioral gap: only ste100's own
hand-written `set_check_config` could validate an extra per-check
parameter (`length`'s word limits), because nobody generalized that
plumbing for the other two. This module is that generalization: a
ruleset now declares a `CheckTable` -- one `Check` per check, carrying
its id, its user-facing text, its default {threshold, action}, and any
of its own tunable params -- and every function below operates on that
declared table plus (project_root, ruleset_id), the same
(ruleset_id, table, project_root, ...) shape core/terms.py already
established for term lists.

`Check.fn`/`unit`/`terms_list`/`terms_arg`/`terms_shape`/`classify`/
`dedup` feed `run_checks()` below -- the generalization of each
ruleset's own `lint_and_gate` dispatch LOOP (call every check's `fn`
against its declared `unit`, file the result as mechanical or
semantic). Text-SPLITTING stays each ruleset's own job on purpose:
sentence tokenization, block-awareness (code fences, list items,
inline-code stripping), and any per-item context a check needs (ste100's
per-sentence procedure/description register, codewatch's per-file
`is_script`) are all genuinely ruleset-specific business logic, not
generic scaffolding -- `run_checks()` only unifies the repetitive
"for v in check_X(...): result.append({...})" boilerplate every
ruleset's lint_and_gate used to hand-write once per check, given
iteration domains (`lines`, `sentences`, `text`) and any per-check
extra argument the ruleset already computed.
"""
from dataclasses import dataclass, field
import inspect
from enum import Enum

from core import config as _core_config
from core.flags import default_label as _default_label, flag_weight


class Unit(Enum):
    """The granularity a check's matcher function operates over --
    consumed by run_checks() below, which dispatches each check against
    the iteration domain matching its own unit."""
    SENTENCE = "sentence"              # fn(sentence, **extras)
    SENTENCES = "sentences"            # fn(all_sentences: list) -- cross-sentence, once/call
    LINE = "line"                      # fn(line, **extras)
    LINE_LOOKAHEAD = "line_lookahead"  # fn(line, next_line)
    LINES_INDEXED = "lines_indexed"    # fn(lines, i) -- needs the whole file + index
    DOCUMENT = "document"              # fn(text, **extras) -- whole/assembled text, once/call
    BLOCK = "block"                    # fn(block_text, **extras) -- once per paragraph/
                                        # list-item block, not the whole document (e.g.
                                        # ste100's safety_instruction, which needs to see
                                        # one block's own text, but has no reason to span
                                        # several -- DOCUMENT would force it to reassemble
                                        # block boundaries itself)


class ExtraArgs(tuple):
    """Wrap extra_by_check[check_id] in this when a check's fn takes MORE
    THAN ONE extra positional argument beyond the item itself (the plain
    single-value case run_checks() has always supported stays the
    default) -- e.g. ste100's vocabulary(sentence, project_terms,
    suppressed). run_checks() unpacks an ExtraArgs as *args instead of
    appending it as one value."""
    def __new__(cls, *values):
        return super().__new__(cls, values)


@dataclass(frozen=True)
class Check:
    """One check's declared identity: what it's called, what it catches,
    its default tuning, and any extra numbers it owns (e.g. ste100's
    `length` carries `procedure_word_limit`/`description_word_limit`).
    `params` is `{name: default_int}` -- a check with none is the common
    case and needs no entry."""
    id: str
    unit: Unit
    fn: object
    catches: str
    instead: str
    default_threshold: int = 1
    default_action: str = "warn"          # "warn" | "block"
    params: dict = field(default_factory=dict)
    terms_list: str = None                # TERM_LISTS key feeding this check, if any
    terms_arg: str = "extra"
    terms_shape: str = "flat"             # "flat" | "with_notes"
    classify: object = "semantic"         # "mechanical" | "semantic" | fn(violation) -> one of those
    dedup: bool = True
    # "tell" | "defect". The distinction that decides what a check's
    # SILENCE means, and the only thing that makes "19 of 31 fired zero
    # times" actionable rather than merely alarming.
    #
    # A TELL is a correlate of machine authorship. It was catalogued
    # against some model at some date, and when it stops firing that is
    # evidence it stopped describing anything -- a prune candidate.
    #
    # A DEFECT is wrong whatever wrote it: an emoji in body text, an em
    # dash written as an HTML entity, a generator's own scaffolding left
    # behind. Silence there means the defect is rare, which is the
    # outcome you wanted. Pruning it would be reading success as failure.
    #
    # Frequency alone cannot separate the two, which is why this is
    # declared rather than measured.
    kind: str = "tell"


CheckTable = dict


def all_check_ids(table):
    return frozenset(table)


def default_check_config(table):
    """`table`'s own declared defaults, in the on-disk {threshold, action,
    **params} shape -- a check with no `params` gets exactly {threshold,
    action}, matching every check's own DEFAULT_CHECK_CONFIG entry today."""
    out = {}
    for check_id, check in table.items():
        spec = {"threshold": check.default_threshold, "action": check.default_action}
        spec.update(check.params)
        out[check_id] = spec
    return out


def check_config(table, project_root, ruleset_id, file_path=None):
    """`default_check_config(table)` with any valid override from
    stopslop.config.json's "check_config" key layered on top, per check.
    An override naming an unknown check, an invalid action, or a
    non-integer/non->=1 number for any other field (threshold, or a
    check's own param) is ignored for that field -- never breaks a live
    gate call on a malformed config. Read fresh every call, the same
    never-cache-it posture every other config read in this project takes."""
    merged = default_check_config(table)
    try:
        overrides = _core_config.check_config_for_path(
            project_root, ruleset_id, file_path)
    except Exception:
        return merged
    for check_id, override in overrides.items():
        if check_id not in merged or not isinstance(override, dict):
            continue
        spec = dict(merged[check_id])
        for name in spec:
            if name == "action":
                if override.get("action") in ("block", "warn"):
                    spec["action"] = override["action"]
                continue
            value = override.get(name)
            if isinstance(value, int) and not isinstance(value, bool) and value >= 1:
                spec[name] = value
        merged[check_id] = spec
    return merged


def enabled_check_ids(table, project_root, ruleset_id, file_path=None):
    all_ids = all_check_ids(table)
    try:
        disabled = set(_core_config.disabled_checks_for_path(project_root, ruleset_id, file_path))
    except Exception:
        return all_ids
    return all_ids - disabled


def list_checks(table, project_root, ruleset_id):
    disabled = set(_core_config.disabled_checks(project_root, ruleset_id))
    return {
        check_id: {"catches": check.catches, "instead": check.instead,
                   "unit": check.unit.value, "enabled": check_id not in disabled}
        for check_id, check in table.items()
    }


def set_enabled_checks(table, project_root, ruleset_id, check_ids):
    """Enable exactly this set of checks (disables every other known
    check) -- REPLACE semantics, for a caller holding the whole picture
    (the CLI's `checks --enable a b c`)."""
    unknown = set(check_ids) - set(table)
    if unknown:
        raise ValueError(f"unknown check id(s): {sorted(unknown)} -- known: {sorted(table)}")
    disabled = sorted(set(table) - set(check_ids))
    _core_config.save_disabled_checks(project_root, ruleset_id, disabled)


def set_checks_enabled(table, project_root, ruleset_id, states):
    """Turn the named checks on or off, leaving every other check alone
    -- MERGE semantics, for a caller holding a partial view (the
    dashboard's Checks table). Collapsing this into set_enabled_checks's
    replace semantics is the exact bug this pair exists to prevent: a
    dashboard save that only saw a filtered subset of rows once silently
    disabled every check outside the filter."""
    unknown = set(states) - set(table)
    if unknown:
        raise ValueError(f"unknown check id(s): {sorted(unknown)} -- known: {sorted(table)}")
    _core_config.merge_disabled_checks(project_root, ruleset_id, states)


def list_check_config(table, project_root, ruleset_id):
    """Every check's own {threshold, action}, current effective value and
    built-in default, plus a "params" dict for a check that declares any
    -- {name: {"value": N, "default": N}}, read by whatever renders that
    check's own detail."""
    current = check_config(table, project_root, ruleset_id)
    out = {}
    for check_id, spec in current.items():
        check = table[check_id]
        entry = {"threshold": spec["threshold"], "action": spec["action"],
                 "default_threshold": check.default_threshold,
                 "default_action": check.default_action}
        if check.params:
            entry["params"] = {name: {"value": spec[name], "default": default}
                                for name, default in check.params.items()}
        out[check_id] = entry
    return out


def set_check_config(table, project_root, ruleset_id, check_id, threshold=None, action=None, **params):
    """Set one check's threshold, action, and/or its own extra params,
    leaving whatever isn't named alone. An unknown check id, an unknown
    param name for that check, or an invalid value for any field raises
    rather than silently writing a field nothing reads."""
    if check_id not in table:
        raise ValueError(f"unknown check id {check_id!r} -- known: {sorted(table)}")
    check = table[check_id]
    unknown = set(params) - set(check.params)
    if unknown:
        raise ValueError(f"unknown setting(s) for {check_id!r}: {sorted(unknown)}"
                          + (f" -- known: {sorted(check.params)}" if check.params
                             else " -- this check has only threshold and action"))
    if threshold is not None and (not isinstance(threshold, int)
                                   or isinstance(threshold, bool) or threshold < 1):
        raise ValueError(f"threshold must be a whole number >= 1, got {threshold!r}")
    if action is not None and action not in ("block", "warn"):
        raise ValueError(f"action must be 'block' or 'warn', got {action!r}")
    for name, value in params.items():
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise ValueError(f"{name} must be a whole number >= 1, got {value!r}")
    spec = dict(_core_config.check_config(project_root, ruleset_id).get(check_id, {}))
    if threshold is not None:
        spec["threshold"] = threshold
    if action is not None:
        spec["action"] = action
    spec.update(params)
    _core_config.save_check_config(project_root, ruleset_id, check_id, spec)


def blocking_semantic_flags(table, project_root, ruleset_id, semantic_flags,
                             file_path=None):
    """Group flags by check, weigh each check's own OCCURRENCES (not its
    deduped display length -- see core.flags.flag_weight) against its own
    threshold, and return the flags of every check that is both
    triggered and set to block. Was three near-identical copies (ste100's
    exclusion-list framing, slopwatch's/codewatch's per-check-threshold
    framing) that turned out to already be the same mechanism.

    `file_path`, when given, layers the matching routing rule's own
    "check_config" over the project-wide one -- so a threshold can differ
    between a reference document and a changelog, which measurement says
    it should, since the human band for a formatting check is not the
    same in both. Omitting it keeps the project-wide answer, which is
    what every caller without a path in hand wants."""
    config = check_config(table, project_root, ruleset_id, file_path)
    grouped = {}
    for f in semantic_flags:
        grouped.setdefault(f["kind"], []).append(f)
    blocking = []
    for check_id, flags in grouped.items():
        spec = config.get(check_id, {"threshold": 1, "action": "warn"})
        if flag_weight(flags) >= spec["threshold"] and spec["action"] == "block":
            blocking.extend(flags)
    return blocking


def run_checks(table, *, blocks=None, lines=None, sentences=None, text=None, extra_by_check=None):
    """Dispatch every check in `table` against the iteration domain
    matching its own `unit`, filing each violation as mechanical or
    semantic -- (mechanical, semantic), the same two flat lists every
    ruleset's lint_and_gate already builds by hand, each entry shaped
    {"kind", "label", "detail", "text"}.

    The CALLER (a ruleset's own lint_and_gate) still owns:
      - computing `blocks`/`lines`/`sentences`/`text` -- whatever text-
        splitting, block-awareness, or tokenization that ruleset's own
        domain needs; a unit with no matching domain supplied here is
        silently skipped (a LINE check when `lines` is None contributes
        nothing -- "no input for this domain" is a normal answer, not an
        error)
      - `extra_by_check`: {check_id: extra_value} for any check whose
        `fn` takes one extra argument beyond the item itself (resolved
        term-list content, a per-file computed value like codewatch's
        is_script) -- passed positionally, so the check's own parameter
        name never has to match anything here; a check_id absent from
        this dict is called with no extra arg at all. `extra_value` may
        also be:
          - an ExtraArgs(...) instance, for a check whose fn takes MORE
            than one extra positional argument (ste100's vocabulary:
            project_terms, suppressed) -- unpacked as *args instead of
            appended as one value
          - a callable, for a per-ITEM extra that varies across the
            domain (ste100's length: the word limit depends on whether
            THIS sentence came from a numbered list item, not a single
            value for the whole call) -- called with the item's own
            index within its domain (blocks/lines/sentences; always 0
            for a DOCUMENT/SENTENCES check, which only ever runs once)
            and the result used exactly as a plain extra_value would be,
            including being an ExtraArgs to unpack
      - enabled-filtering and dedup on the returned lists, exactly as
        every ruleset's lint_and_gate already does after its own
        hand-written loop today -- neither is this function's job

    `label` is core.flags.default_label(violation) -- whichever of
    "word"/"phrase"/"modal"/"label" the violation carries, or None
    (matching every hand-written call site's own label choice today,
    including the document-level checks that pass label=None because
    their violation dict carries none of those keys).

    `check.classify` decides the mechanical/semantic bucket -- a literal
    ("mechanical"/"semantic", the common case) or a callable taking one
    violation dict and returning one of those two strings, for a check
    whose classification depends on the violation itself (e.g. ste100's
    vocabulary: auto-fixable substitutions are mechanical, everything
    else is semantic).

    ITERATION ORDER matches every hand-written loop this replaces: the
    OUTER loop is over items (block 0, block 1, ... / line 0, line 1,
    ... / sentence 0, sentence 1, ...), the INNER loop is over checks in
    `table`'s own declaration order -- a hand-written loop calls
    check_a(line) then check_b(line) for EVERY line before moving to the
    next line, not every line for check_a before starting check_b. The
    BLOCK domain, when supplied, is dispatched before LINE/SENTENCE/
    DOCUMENT -- matching every ruleset that needs it, which collects its
    block-level flags during its own block-splitting loop, before any
    per-sentence work starts. A caller whose denial message shows the
    first few flags, or whose test pins exact output order, depends on
    this -- reordering silently would be a real behavior change wearing
    a refactor's clothes."""
    extra_by_check = extra_by_check or {}
    mechanical, semantic = [], []

    def _classify(check, violation):
        c = check.classify
        return c(violation) if callable(c) else c

    def _file(check, violation, text_value):
        entry = {"kind": check.id, "label": _default_label(violation),
                  "detail": violation, "text": text_value}
        (mechanical if _classify(check, violation) == "mechanical" else semantic).append(entry)

    def _resolve_extra(check, index):
        extra = extra_by_check[check.id]
        return extra(index) if callable(extra) and not isinstance(extra, ExtraArgs) else extra

    def _call(check, index, *args):
        if check.id not in extra_by_check:
            return check.fn(*args)
        extra = _resolve_extra(check, index)
        return check.fn(*args, *extra) if isinstance(extra, ExtraArgs) else check.fn(*args, extra)

    if blocks is not None:
        for i, block in enumerate(blocks):
            for check in table.values():
                if check.unit == Unit.BLOCK:
                    for v in _call(check, i, block):
                        _file(check, v, block)

    if lines is not None:
        for i, line in enumerate(lines):
            for check in table.values():
                if check.unit == Unit.LINE:
                    for v in _call(check, i, line):
                        _file(check, v, line)
                elif check.unit == Unit.LINE_LOOKAHEAD:
                    next_line = lines[i + 1] if i + 1 < len(lines) else None
                    for v in check.fn(line, next_line):
                        _file(check, v, line)
                elif check.unit == Unit.LINES_INDEXED:
                    for v in check.fn(lines, i):
                        _file(check, v, line)

    if sentences is not None:
        for i, s in enumerate(sentences):
            for check in table.values():
                if check.unit == Unit.SENTENCE:
                    for v in _call(check, i, s):
                        _file(check, v, s)
        for check in table.values():
            if check.unit == Unit.SENTENCES:
                for v in check.fn(sentences):
                    _file(check, v, v.get("text"))

    if text is not None:
        for check in table.values():
            if check.unit == Unit.DOCUMENT:
                for v in _call(check, 0, text):
                    _file(check, v, None)

    return mechanical, semantic


def call_blocking_semantic_flags(ruleset, semantic_flags, file_path=None):
    """Call a ruleset's `blocking_semantic_flags`, with or without a path.

    `file_path` is a LATER addition to the ruleset contract, added so a
    routing rule can carry its own per-check thresholds. Custom rulesets
    are a shipped feature and live under `.claude/stopslop/`, outside
    this repository -- one written against the older two-name signature
    must keep working, and it must keep working SILENTLY, because a
    project author who scaffolded a ruleset months ago did nothing wrong.

    The signature is inspected rather than caught: wrapping the call in
    `except TypeError` would swallow a TypeError raised INSIDE a check
    and report it as an old signature, which is the kind of misdiagnosis
    that costs an afternoon.
    """
    fn = ruleset.blocking_semantic_flags
    try:
        takes_path = len(inspect.signature(fn).parameters) >= 2
    except (TypeError, ValueError):
        takes_path = False
    if takes_path:
        return fn(semantic_flags, file_path)
    return fn(semantic_flags)
