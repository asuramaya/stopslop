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
`dedup` are recorded here for a possible future unification of each
ruleset's own `lint_and_gate` text-splitting/orchestration loop --
genuinely different splitting logic (sentence-level with a word-limit
context vs. line-level with lookahead) makes that a separate, harder
piece of work. Nothing in this module reads those fields yet; each
ruleset's `lint_and_gate` stays hand-written and calls its own
`check_*` functions directly, unchanged. Only the scaffolding below --
which never needed to know how a check's matcher works, only its id,
text, and tunable numbers -- is unified now.
"""
from dataclasses import dataclass, field
from enum import Enum

from core import config as _core_config
from core.flags import flag_weight


class Unit(Enum):
    """The granularity a check's matcher function operates over. Not yet
    consumed by anything here -- see the module docstring."""
    SENTENCE = "sentence"              # fn(sentence, **extras)
    SENTENCES = "sentences"            # fn(all_sentences: list) -- cross-sentence, once/call
    LINE = "line"                      # fn(line, **extras)
    LINE_LOOKAHEAD = "line_lookahead"  # fn(line, next_line)
    LINES_INDEXED = "lines_indexed"    # fn(lines, i) -- needs the whole file + index
    DOCUMENT = "document"              # fn(text, **extras) -- whole/assembled text, once/call


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


def check_config(table, project_root, ruleset_id):
    """`default_check_config(table)` with any valid override from
    stopslop.config.json's "check_config" key layered on top, per check.
    An override naming an unknown check, an invalid action, or a
    non-integer/non->=1 number for any other field (threshold, or a
    check's own param) is ignored for that field -- never breaks a live
    gate call on a malformed config. Read fresh every call, the same
    never-cache-it posture every other config read in this project takes."""
    merged = default_check_config(table)
    try:
        overrides = _core_config.check_config(project_root, ruleset_id)
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
                   "enabled": check_id not in disabled}
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


def blocking_semantic_flags(table, project_root, ruleset_id, semantic_flags):
    """Group flags by check, weigh each check's own OCCURRENCES (not its
    deduped display length -- see core.flags.flag_weight) against its own
    threshold, and return the flags of every check that is both
    triggered and set to block. Was three near-identical copies (ste100's
    exclusion-list framing, slopwatch's/codewatch's per-check-threshold
    framing) that turned out to already be the same mechanism."""
    config = check_config(table, project_root, ruleset_id)
    grouped = {}
    for f in semantic_flags:
        grouped.setdefault(f["kind"], []).append(f)
    blocking = []
    for check_id, flags in grouped.items():
        spec = config.get(check_id, {"threshold": 1, "action": "warn"})
        if flag_weight(flags) >= spec["threshold"] and spec["action"] == "block":
            blocking.extend(flags)
    return blocking
