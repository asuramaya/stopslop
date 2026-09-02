"""Path -> ruleset resolution.

A project's `stopslop.config.json` (repo root, sibling to stopslop.py) maps
glob patterns to a ruleset id, first-match-wins -- the same override-list
shape ESLint's `overrides` uses. Lives at the repo root rather than under
`.claude/` on purpose: `.claude/settings.local.json` is per-clone machine
wiring (hook command paths templated for one checkout, gitignored); this is
project-level policy the CLI and MCP server need with no live Claude Code
session at all, closer to `.eslintrc` or `pyproject.toml`.

With no config file present, DEFAULT_RULES originally reproduced exactly
what pretool_hook.py's `in_scope()` did before rulesets existed: STE100 on
.md/.txt/.rst, `.claude/` out of scope entirely -- a required invariant at
the time (a ruleset existing in the code registry must never *accidentally*
change behavior for a clone with no config file, just because it got
registered). codewatch and slopwatch have since been validated against
this project's own real files (stopslop.py scan, not synthetic fixtures --
see docs/ for both rulesets' own false-positive fixes found that way), so
the baseline default is now a deliberate, tested choice rather than that
original invariant.

That choice REVERSED once, and the reason matters more than the rules do.
ste100 used to hold every `.md`/`.txt`/`.rst` file, with the repo-root
`README.md` carved out to slopwatch as prose "meant to read like a person
wrote it". That carve-out states the right principle and then applies it
to exactly one file. ASD-STE100 is a controlled language for maintenance
procedures, where one reading of a sentence has to be the only reading,
and it buys that with a deliberate monotone: short declaratives, one
tense, roughly 875 approved words. That is correct for a procedure a
technician follows at 3am. It is a category error for a README, a design
note, or a security policy, and the monotone it enforces is close kin to
the flat generated register this project exists to catch. The tool proved
this on itself: ste100 called 23 sentences of SECURITY.md blocking
failures over the words "blocking", "warning" and "reading", none of which
that document can avoid.

So prose defaults to slopwatch, which asks "does this read like filler",
a question worth asking of any `.md`. ste100 is opt-in, for the text it
was built for -- add a rule naming your procedures, e.g.
{"glob": "docs/runbooks/*.md", "ruleset": "ste100"}, ABOVE the general
`*.md` rule, since first-match-wins checks rules in order, top to bottom.
`*.py` routes to codewatch, this project's own primary language.

This module has no dependency on `rulesets` (the registry) -- it only ever
resolves a path to a bare ruleset id string via `resolve_ruleset_id`, or to a
live module via `resolve_ruleset` given a registry passed in by the caller.
Keeping it dependency-free is what lets it stay in `core/` as pure library
code, importable by both rulesets and the orchestrator scripts without ever
risking an import cycle.
"""
import fnmatch
import json
import os
import re

# Free text (CLI stdin, an MCP lint_text call, the dashboard playground) has
# no real file to route on, so every entry point treats it as if written to
# this name at the repo root -- reusing the one real config-driven resolver
# instead of each growing its own "default ruleset" fallback that could drift
# from it. Defined here, next to the resolver, because stopslop.py and
# mcp_server.py each used to carry their own copy of the literal.
SYNTHETIC_TEXT_NAME = "__stdin__.md"

DEFAULT_RULES = [
    {"glob": ".claude/*", "ruleset": None},
    {"glob": "*.md", "ruleset": "slopwatch"},
    {"glob": "*.txt", "ruleset": "slopwatch"},
    {"glob": "*.rst", "ruleset": "slopwatch"},
    {"glob": "*.py", "ruleset": "codewatch"},
]


def config_path(project_root):
    return os.path.join(project_root, "stopslop.config.json")


def load_rules(project_root, config_file=None):
    """The parsed rule list, or DEFAULT_RULES if no config file exists. No
    caching -- read fresh every call. A stale in-memory copy inside a
    long-running process (the MCP server) is exactly the bug class a
    project-glossary registration hit earlier in this project's history;
    config resolution gets the same never-cache treatment from day one
    rather than repeating that mistake."""
    path = config_file or config_path(project_root)
    if not os.path.exists(path):
        return DEFAULT_RULES
    with open(path) as f:
        data = json.load(f)
    return data.get("rulesets", DEFAULT_RULES)


def packs_for_path(project_root, file_path=None, list_id=None, config_file=None):
    """Which vocabulary packs apply to one file, for one term list, read off
    the SAME first-match-wins routing rule that decides which ruleset gates
    it:

        {"glob": "docs/security/**", "ruleset": "ste100",
         "packs": {"project_terms": ["nist-security"]}}

    Two things are deliberate about that shape.

    First, packs hang off the PATH. They used to hang off a ruleset id
    ("glossary_packs": {"ste100": [...]}), which threw the path away -- and
    since one ruleset handles all prose, that forced the pack list to be
    the union of every domain in the repo. A pack is domain content: NIST
    security vocabulary is right for docs/security/ and wrong for blog/.
    Domain is a property of the TEXT.

    Second, the rule names WHICH LIST each pack feeds. The pack itself does
    not say. A pack is a body of words from a source -- the MDN glossary is
    not ste100 content, it is vocabulary ste100 happens to read as an allow
    list. Letting the pack name its own consumer meant one pack could never
    feed two rulesets, never feed two lists, and never be read at the
    opposite polarity. See core/glossary_packs/__init__.py.

    Deliberately not a cascade. There is no machine-global tier and no
    project-wide-plus-ruleset merge: exactly one rule matches, and that one
    rule fully explains why a word passed in a given file. A cascade would
    make "why did this word pass?" require merging several sources, one of
    them outside the repo -- gate decisions would stop being locally
    explainable, which is strictly worse than this flat shape.

    `file_path` None means "no particular file" (free text through the CLI
    or the dashboard playground) and resolves against the same synthetic
    path every other free-text entry point already uses, so there is one
    resolution mechanism rather than a second default that could drift.
    `list_id` None returns every pack the rule names, across all lists."""
    if file_path is None:
        file_path = os.path.join(project_root, SYNTHETIC_TEXT_NAME)
    rule = matching_rule(file_path, project_root, config_file)
    return _packs_of(rule, list_id) if rule else []


def _packs_of(rule, list_id=None):
    """The pack ids a rule names, for one list or across all of them.
    Tolerates a rule with no "packs" key at all (the common case)."""
    packs = rule.get("packs") or {}
    if not isinstance(packs, dict):
        return []       # a malformed value contributes nothing, never raises
    if list_id is not None:
        return list(packs.get(list_id, []))
    seen = []
    for ids in packs.values():
        for pack_id in ids:
            if pack_id not in seen:
                seen.append(pack_id)
    return seen


def rule_packs(project_root, config_file=None):
    """[(glob, ruleset_id, {list_id: [pack_id, ...]}), ...] for every
    routing rule -- the whole-project view the Vocabulary tab needs to show
    which packs feed which list where, without picking one file to resolve
    against."""
    out = []
    for rule in load_rules(project_root, config_file):
        packs = rule.get("packs") or {}
        if not isinstance(packs, dict):
            packs = {}
        out.append((rule["glob"], rule["ruleset"],
                     {k: list(v) for k, v in packs.items() if v}))
    return out


def set_rule_packs(project_root, glob, list_id, pack_ids, known_packs=None,
                    config_file=None, admissible=None):
    """Point a set of packs at one term list, on the routing rule with this
    exact glob. Validates every pack id against `known_packs` when given --
    the same loud-on-typo guarantee save_rules already applies to ruleset
    ids, for the same reason: a typo'd name in a committed config is how a
    gate silently stops doing what its owner believes it does.

    Nothing here checks that `list_id` is a list the rule's ruleset
    actually declares. That is on purpose: this module stays free of any
    dependency on the ruleset registry (see the module docstring), and an
    unknown list id is inert -- no list ever asks for it, so it contributes
    nothing. The callers that DO have a registry (the CLI, the dashboard,
    the MCP server) offer only real list ids in the first place."""
    if known_packs is not None:
        for pack_id in pack_ids:
            if pack_id not in known_packs:
                raise ValueError(
                    f"no glossary pack registered as {pack_id!r} -- "
                    f"known: {sorted(known_packs)}")
    # Loud at WRITE time, for the same reason a typo'd ruleset id is: a
    # binding that can never usefully fire is a gate quietly not doing what
    # its owner believes. `admissible` is passed in by the caller that has a
    # registry (this module deliberately has none), and is called with each
    # pack id -- returning (ok, reason).
    if admissible is not None:
        for pack_id in pack_ids:
            ok, why = admissible(pack_id)
            if not ok:
                raise ValueError(f"{pack_id!r} cannot feed {list_id!r}: {why}")
    path = config_file or config_path(project_root)
    data = {}
    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
    rules = [dict(r) for r in data.get("rulesets", DEFAULT_RULES)]
    if not any(r["glob"] == glob for r in rules):
        raise ValueError(f"no routing rule with glob {glob!r} -- "
                          f"known: {[r['glob'] for r in rules]}")
    for rule in rules:
        if rule["glob"] != glob:
            continue
        packs = dict(rule.get("packs") or {})
        if not isinstance(rule.get("packs") or {}, dict):
            packs = {}
        if pack_ids:
            packs[list_id] = list(pack_ids)
        else:
            packs.pop(list_id, None)
        if packs:
            rule["packs"] = packs
        else:
            rule.pop("packs", None)
    data["rulesets"] = rules
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def set_rule_disable(project_root, glob, check_ids, known_checks=None,
                      config_file=None):
    """Replace the "disable" list on the routing rule with this exact glob
    -- the per-path check exemptions disabled_checks_for_path unions in.
    Same shape and same guarantees as set_rule_packs: loud on an unknown
    glob, loud on an unknown check id when the caller supplies
    `known_checks` (this module deliberately has no ruleset registry of
    its own), and an empty list removes the key rather than writing an
    empty one."""
    check_ids = list(check_ids)
    if known_checks is not None:
        for check_id in check_ids:
            if check_id not in known_checks:
                raise ValueError(
                    f"no check registered as {check_id!r} on this rule's "
                    f"ruleset(s) -- known: {sorted(known_checks)}")
    path = config_file or config_path(project_root)
    data = {}
    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
    rules = [dict(r) for r in data.get("rulesets", DEFAULT_RULES)]
    if not any(r["glob"] == glob for r in rules):
        raise ValueError(f"no routing rule with glob {glob!r} -- "
                          f"known: {[r['glob'] for r in rules]}")
    for rule in rules:
        if rule["glob"] != glob:
            continue
        if check_ids:
            rule["disable"] = check_ids
        else:
            rule.pop("disable", None)
    data["rulesets"] = rules
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def disabled_checks(project_root, ruleset_id, config_file=None):
    """Which individual checks are turned off for `ruleset_id`, per
    stopslop.config.json's "disabled_checks" key: {"<ruleset_id>":
    ["<check_id>", ...]}. Opposite default from glossary packs on purpose:
    a check exists to catch something by default, so this key is an
    opt-OUT list, not an opt-in one -- empty (nothing disabled, every
    check runs) with no config file, matching the DEFAULT_RULES/no-config
    invariant every other knob in this file already gives."""
    path = config_file or config_path(project_root)
    if not os.path.exists(path):
        return []
    with open(path) as f:
        data = json.load(f)
    return data.get("disabled_checks", {}).get(ruleset_id, [])


def save_disabled_checks(project_root, ruleset_id, check_ids, config_file=None):
    """Write which checks are disabled for `ruleset_id`, preserving every
    other top-level key already in the file -- same clobber-avoidance
    shape as save_glossary_packs/save_rules."""
    path = config_file or config_path(project_root)
    data = {}
    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
    data.setdefault("disabled_checks", {})[ruleset_id] = check_ids
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def disabled_checks_for_path(project_root, ruleset_id, file_path=None,
                              config_file=None):
    """Checks turned off for `ruleset_id`, project-wide PLUS whatever the
    routing rule matching `file_path` names in its own "disable" list.

    Symmetric with packs, and for the same reason. A ruleset's checks are a
    project-wide setting, but "not this one, not in this directory" is a
    real need that whole-file exemption answers too bluntly: routing a path
    to `"ruleset": null` already exempts a file, and that turns off ALL
    checking rather than the one check that misfires. codewatch denying its
    own test file (a fixture full of deliberately bad code) is the standing
    example -- the fix should be "swallowed_exception does not apply to
    fixtures", not "stop checking this file at all".

        {"glob": "tests/**", "ruleset": "codewatch",
         "disable": ["swallowed_exception"]}

    Union, never subtraction: a rule can turn a check OFF for its paths, and
    cannot turn one back on that the project disabled globally. One
    direction keeps "why did this not fire here?" answerable from two
    places at most, and keeps the rule from silently re-enabling something
    a project deliberately switched off.

    A rule's "disable" list applies to EVERY ruleset the rule invokes on
    its paths -- the host and, since embedded prose arrived, the
    embedded_prose ruleset too. The need showed up on day one of
    dogfooding: colon_reveal is a real prose check that reads code
    strings as one long false positive ("Usage:", "Not saved:",
    "default:" are labels, not buildup-and-reveal), and per-path
    disabling is exactly the mechanism for "this check does not apply in
    this context"."""
    disabled = set(disabled_checks(project_root, ruleset_id, config_file))
    rule = matching_rule(file_path, project_root, config_file) if file_path else None
    if rule and ruleset_id in (rule.get("ruleset"), rule.get("embedded_prose")):
        extra = rule.get("disable") or []
        if isinstance(extra, list):
            disabled |= set(extra)
    return sorted(disabled)


def merge_disabled_checks(project_root, ruleset_id, states, config_file=None):
    """Turn the named checks on or off, leaving every check not named alone.
    `states` is {check_id: bool}. Returns the resulting disabled list.

    The sibling of save_disabled_checks, which REPLACES. Both shapes are
    legitimate and the choice is not cosmetic: a caller that holds the whole
    picture (the CLI's `checks --enable a b c`, which means "these and only
    these") wants replace, and a caller holding a PARTIAL view wants merge.

    This exists because the dashboard was the second kind using the first
    kind's call. Its Checks table has a search box, and it saved whatever
    rows survived the filter -- so typing "filler" and pressing Save read as
    "enable exactly filler_opener and filler_verb" and turned off the other
    18 slopwatch checks, with a success toast and no way to notice. The
    caller was wrong, but a call that quietly interprets a partial list as a
    total one will keep being got wrong; a merge-shaped call cannot be.
    Validation of the ids stays with the ruleset, which is the only layer
    that knows what checks it has."""
    disabled = set(disabled_checks(project_root, ruleset_id, config_file))
    for check_id, enabled in states.items():
        disabled.discard(check_id) if enabled else disabled.add(check_id)
    ordered = sorted(disabled)
    save_disabled_checks(project_root, ruleset_id, ordered, config_file)
    return ordered


def check_config(project_root, ruleset_id, config_file=None):
    """Per-check {"threshold": N, "action": "block"|"warn"} overrides for
    `ruleset_id`, per stopslop.config.json's "check_config" key:
    {"<ruleset_id>": {"<check_id>": {"threshold": N, "action": ...}}}.
    Empty with no config file, or no entry -- a ruleset's own hardcoded
    per-check defaults keep governing an unconfigured clone, the same
    invariant every other knob in this file gives.

    Replaces the old shared ruleset-wide block_flag_count_threshold plus
    a hardcoded, non-configurable BLOCKS_ALONE_AT: every check now owns
    its own threshold and its own block/warn action, both real project
    settings instead of one shared number and one thing only code could
    change."""
    path = config_file or config_path(project_root)
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        data = json.load(f)
    return data.get("check_config", {}).get(ruleset_id, {})


def save_check_config(project_root, ruleset_id, check_id, spec, config_file=None):
    """Write ONE check's {threshold, action} override, merging into
    whatever the ruleset already has for its OTHER checks -- never a
    replace-the-whole-ruleset write, since a caller edits one row (one
    check) at a time and every other row's override must survive, same
    clobber-avoidance shape as save_disabled_checks."""
    path = config_file or config_path(project_root)
    data = {}
    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
    data.setdefault("check_config", {}).setdefault(ruleset_id, {})[check_id] = spec
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def custom_term_lists(project_root, ruleset_id, config_file=None):
    """This project's own term-list DECLARATIONS for `ruleset_id`, per
    stopslop.config.json's "custom_term_lists" key: {"<ruleset_id>":
    {"<list_id>": {"label", "polarity", "accepts_additions",
    "accepts_packs", "content_kind"}}}. Pure JSON data -- unlike a
    built-in ruleset's own TERM_LISTS entry, a custom one can never carry
    a `pack_admissible` callable (there is no way to express a Python
    predicate here); see effective_term_lists() for the merge with a
    ruleset's code-defined lists."""
    path = config_file or config_path(project_root)
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        data = json.load(f)
    return data.get("custom_term_lists", {}).get(ruleset_id, {})


def save_custom_term_list(project_root, ruleset_id, list_id, spec, config_file=None):
    """Register (or replace) one custom term list's declaration, merging
    into whatever the ruleset already has for its OTHER custom lists --
    same clobber-avoidance shape as save_check_config."""
    path = config_file or config_path(project_root)
    data = {}
    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
    data.setdefault("custom_term_lists", {}).setdefault(ruleset_id, {})[list_id] = spec
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


_CUSTOM_LIST_ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def add_custom_term_list(project_root, ruleset_id, list_id, built_in_lists, label=None,
                          polarity="deny", accepts_additions=True, accepts_packs=False,
                          content_kind="word", feeds=None, config_file=None):
    """Validate-then-save a new custom term list declaration -- the one
    place this validation lives, called by the webui, the CLI, and the
    MCP server alike, so a bad id/collision is refused identically no
    matter which surface asked. `built_in_lists` is the target ruleset's
    own module.TERM_LISTS (the caller's own picture, not fetched here, to
    keep this module dependency-free of the `rulesets` package -- same
    reason save_rules takes a `registry` parameter instead of importing
    one). Refuses an id that isn't lowercase/snake_case, one colliding
    with a built-in list, or one already declared as a custom list on
    this ruleset (use save_custom_term_list directly to replace one)."""
    list_id = list_id.strip().lower()
    if not _CUSTOM_LIST_ID_RE.match(list_id):
        raise ValueError(
            f"list id {list_id!r} must start with a letter, lowercase "
            f"letters/digits/underscores only (e.g. 'internal_jargon')")
    if list_id in built_in_lists:
        raise ValueError(f"{list_id!r} is a built-in list on {ruleset_id!r} -- choose a different id")
    if list_id in custom_term_lists(project_root, ruleset_id, config_file=config_file):
        raise ValueError(f"a custom list {list_id!r} already exists on {ruleset_id!r} "
                          f"-- remove it first to replace it")
    spec = {
        "label": (label or list_id).strip(),
        "polarity": polarity if polarity in ("allow", "deny") else "deny",
        "accepts_additions": bool(accepts_additions),
        "accepts_packs": bool(accepts_packs),
        "content_kind": (content_kind or "word").strip(),
    }
    if feeds:
        spec["feeds"] = feeds
    save_custom_term_list(project_root, ruleset_id, list_id, spec, config_file=config_file)
    return spec


def set_custom_term_list_feeds(project_root, ruleset_id, list_id, feeds, config_file=None):
    """Bind (or, with feeds=None, unbind) an existing custom list to the
    custom check it feeds -- the same list-declares-the-check-it-feeds
    direction a built-in list's own TERM_LISTS entry already uses (see
    core/terms.py's own note on why the binding lives on the list, not
    the check). Set from the CHECK side (routes_checks.py's add/update/
    remove), since the list already exists by the time a check is
    created or edited and choosing to bind it. Only a CUSTOM list's spec
    can be rewritten this way -- a built-in one lives in a ruleset's own
    Python source, immutable from here, and already has its own fixed
    feeds target."""
    lists = custom_term_lists(project_root, ruleset_id, config_file=config_file)
    if list_id not in lists:
        raise ValueError(f"no custom list {list_id!r} on {ruleset_id!r} to bind")
    spec = dict(lists[list_id])
    if feeds:
        spec["feeds"] = feeds
    else:
        spec.pop("feeds", None)
    save_custom_term_list(project_root, ruleset_id, list_id, spec, config_file=config_file)
    return spec


def clear_feeds_for_check(project_root, ruleset_id, check_id, config_file=None):
    """Unbind whichever custom list currently feeds `check_id`, if any --
    called when that check is removed, so a term list is never left
    pointing at a check id that no longer exists (the "a guard that
    validates at creation time does not protect what already exists"
    trap: a stale feeds pointer would silently resolve to nothing at
    lint time today, but there is no reason to leave it dangling for
    whatever reads it next). A no-op if nothing was bound to it."""
    for list_id, spec in custom_term_lists(project_root, ruleset_id, config_file=config_file).items():
        if spec.get("feeds") == check_id:
            set_custom_term_list_feeds(project_root, ruleset_id, list_id, None, config_file=config_file)


def check_terms_list_available(project_root, ruleset_id, check_id, terms_list, config_file=None):
    """Read-only half of binding a custom check to a vocabulary list:
    raises if `terms_list` already feeds a DIFFERENT check, rather than
    silently reassigning it (mirrors add_custom_check's own id-collision
    refusal one level up). The shared entry point for the CLI, MCP
    server, and webui alike -- call this BEFORE the check file itself is
    written, so a conflict here never creates a check whose vocabulary
    binding then fails; true validate-then-write for the whole add/
    update, not just the file. A no-op (never raises) when `terms_list`
    is falsy -- an unbind is always available."""
    terms_list = terms_list or None
    if not terms_list:
        return
    feeds = custom_term_lists(project_root, ruleset_id, config_file=config_file).get(terms_list, {}).get("feeds")
    if feeds not in (None, check_id):
        raise ValueError(f"list {terms_list!r} already feeds check {feeds!r} "
                          f"-- unbind it there first")


def apply_terms_list_binding(project_root, ruleset_id, check_id, terms_list, config_file=None):
    """The write half: call only after the check file itself saved
    successfully (and only after check_terms_list_available already
    passed), so this never fails on a conflict -- it just moves the
    pointer, unbinding whatever the check used to feed first. Pass
    terms_list=None (or "") to unbind with no new binding."""
    clear_feeds_for_check(project_root, ruleset_id, check_id, config_file=config_file)
    if terms_list:
        set_custom_term_list_feeds(project_root, ruleset_id, terms_list, check_id, config_file=config_file)


def delete_custom_term_list(project_root, ruleset_id, list_id, config_file=None):
    """Remove one custom term list's DECLARATION. Its own project-layer
    terms (added via add_term while the list was declared) are orphaned,
    not deleted -- the same "removal is reversible, never silent data
    loss" posture every other removal in this project already takes;
    re-declaring the same ruleset_id/list_id later makes them reappear.
    Returns False if there was nothing to remove (an unknown list_id),
    True otherwise -- a caller decides what that means, this layer just
    reports it truthfully."""
    path = config_file or config_path(project_root)
    if not os.path.exists(path):
        return False
    with open(path) as f:
        data = json.load(f)
    lists = data.get("custom_term_lists", {}).get(ruleset_id, {})
    if list_id not in lists:
        return False
    del lists[list_id]
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    return True


def effective_term_lists(base_term_lists, ruleset_id, project_root, config_file=None):
    """A ruleset's own code-defined TERM_LISTS, plus this project's own
    custom_term_lists declarations for it -- read fresh every call, same
    never-cache-it posture every other config read in this project takes
    (a long-running dashboard process must see a custom list on the very
    next render after adding it, no restart). A custom list can never
    shadow a built-in one; the built-in wins on a colliding id, the same
    refuse-rather-than-shadow posture core.glossary_packs.add_pack
    already gives a custom pack colliding with a built-in one."""
    merged = dict(base_term_lists)
    for list_id, spec in custom_term_lists(project_root, ruleset_id, config_file).items():
        if list_id not in merged:
            merged[list_id] = spec
    return merged


# Every top-level key a current reader in this module actually consumes.
# A key outside this set is not "extra" -- it is DEAD: something used to
# read it, stopped, and the write side that produced it (an old CLI flag,
# an old dashboard control) is gone too, so nothing will ever write it
# again either. `stray_top_level_keys` exists because this already
# happened silently once: the "options" capability (a ruleset-wide
# {block_flag_count_threshold: N} knob) was deleted in favor of per-check
# {threshold, action}, and a project's own `stopslop.config.json` kept its
# old "options" key -- sitting there looking active, tuning nothing,
# with no reader anywhere left to warn its owner it had gone inert.
KNOWN_TOP_LEVEL_KEYS = frozenset({"rulesets", "terms", "disabled_checks", "check_config",
                                   "custom_term_lists"})


def stray_top_level_keys(project_root, config_file=None):
    """Top-level keys in stopslop.config.json that no reader in this
    module consumes -- see KNOWN_TOP_LEVEL_KEYS. Empty list with no config
    file, the same no-config-means-nothing-to-warn-about baseline every
    other knob here gives."""
    path = config_file or config_path(project_root)
    if not os.path.exists(path):
        return []
    with open(path) as f:
        data = json.load(f)
    return sorted(set(data) - KNOWN_TOP_LEVEL_KEYS)


def strip_top_level_keys(project_root, keys, config_file=None):
    """Delete the named top-level keys from stopslop.config.json, leaving
    everything else untouched. For discarding exactly what
    stray_top_level_keys just found -- never called with a key still in
    KNOWN_TOP_LEVEL_KEYS, so this does not need to re-validate that."""
    path = config_file or config_path(project_root)
    data = {}
    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
    for key in keys:
        data.pop(key, None)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def _relative_posix_path(file_path, project_root):
    """The path relative to project_root, using '/' regardless of platform
    (fnmatch patterns in config files are always written with '/'). Returns
    None if file_path isn't actually under project_root at all -- out of
    scope, not an error."""
    try:
        rel = os.path.relpath(file_path, project_root)
    except ValueError:
        return None  # e.g. different drive on Windows -- not comparable
    if rel == os.curdir or rel.startswith(os.pardir):
        return None if rel.startswith(os.pardir) else ""
    return rel.replace(os.sep, "/")


def matching_rule(file_path, project_root, config_file=None):
    """The ONE rule that decides this path -- the whole rule dict, or None
    if nothing matched.

    First-match-wins is this project's central promise: exactly one rule
    explains a file's ruleset, its packs, and therefore why a given word
    passed in it. The promise only holds if every caller asks the question
    the way the gate asks it. The dashboard used to run its own fnmatch loop
    to find a rule to hang a pack on -- the first rule matching both the
    path AND a chosen ruleset, which can select a rule the gate never
    reaches: `README.md` routes to slopwatch in this repo's own config, so
    attaching an ste100 pack "for README.md" found the later `*.md` rule and
    wrote a binding that could not ever fire. One resolver, used by
    everyone, makes that unrepresentable rather than merely unlikely."""
    rel = _relative_posix_path(file_path, project_root)
    if rel is None:
        return None
    for rule in load_rules(project_root, config_file):
        if fnmatch.fnmatch(rel, rule["glob"]):
            return rule
    return None


def resolve_ruleset_id(file_path, project_root, config_file=None):
    """The bare ruleset id a path resolves to, or None if out of scope
    (either no rule matched, or the matching rule's ruleset is explicitly
    null). Does not touch the ruleset registry at all -- split out from
    resolve_ruleset() so callers that only need the id (e.g.
    bash_write_detect's scope check) don't need a live registry, and so this
    half stays testable with zero rulesets registered anywhere."""
    rule = matching_rule(file_path, project_root, config_file)
    return rule["ruleset"] if rule else None


def resolve_ruleset(file_path, project_root, registry, config_file=None):
    """The resolved ruleset MODULE, or None if out of scope. `registry` is
    the `rulesets` package (or anything exposing the same `get_ruleset`/
    `UnknownRulesetError` shape) -- passed in, not imported, so this module
    stays dependency-free. Raises registry.UnknownRulesetError if a rule
    names an id the registry doesn't know: loud on purpose. A typo'd
    ruleset name in a committed config is exactly the silent
    gate-goes-off failure mode this project already hit once (the .dat
    bypass incident, see docs/incidents/) -- resolving to None instead of
    raising would repeat it in a new shape."""
    ruleset_id = resolve_ruleset_id(file_path, project_root, config_file)
    if ruleset_id is None:
        return None
    return registry.get_ruleset(ruleset_id)


def save_rules(project_root, rules, registry, config_file=None):
    """Write `rules` (a list of {"glob", "ruleset"} dicts, the same shape
    DEFAULT_RULES uses) to the config file, after validating every non-null
    ruleset id against `registry` -- the same loud-on-typo guarantee
    resolve_ruleset() already gives a live gate call, applied at write time
    instead of read time so a bad id never reaches disk in the first place.
    The one caller today is the dashboard's config editor; a raw file write
    from there would skip this check entirely. Preserves every other top-
    level key already in the file -- a blind overwrite here would be the
    exact settings.local.json-clobber bug this project already found and
    fixed once in stopslop.py's own init --force, now with a second config
    file it could happen to again.

    A rule carries more than glob and ruleset now -- packs, a per-rule
    "disable" list, an "embedded_prose" ruleset -- so the same clobber
    risk exists one level down: a caller that edits routing without
    knowing about those keys (the routing editor is a separate widget)
    would silently drop them. An incoming rule that says nothing about a
    key therefore INHERITS whatever the rule with that glob already had;
    only an explicit key changes it. Generalized from a packs-only
    carve-out after "embedded_prose" arrived and would have been the
    second key to hit the identical bug ("disable" was already exposed,
    unnoticed).

    A carried-forward pack or disable entry is a list_id or check_id that
    belonged to whatever ruleset this glob pointed at BEFORE. If this
    call is also the one changing the glob's ruleset or embedded_prose
    cell, that entry may name a list or check the rule's NEW ruleset(s)
    have never heard of -- inert the instant it lands, the same "still
    there, still looks live, reads nothing" shape orphaned_rule_extras
    detects after the fact. Re-validated here, at the one write path
    that can actually cause it, rather than left for that read-side
    check to find later: only entries that still fit survive the
    carry-forward."""
    from core import extract as core_extract

    existing_extras = {}
    existing_scope = {}
    path = config_file or config_path(project_root)
    data = {}
    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
        for rule in data.get("rulesets", []):
            existing_scope[rule["glob"]] = (rule.get("ruleset"), rule.get("embedded_prose"))
            extras = {k: v for k, v in rule.items() if k not in ("glob", "ruleset")}
            if extras:
                existing_extras[rule["glob"]] = extras

    merged = []
    for rule in rules:
        if "glob" not in rule or "ruleset" not in rule:
            raise ValueError(f"rule {rule!r} needs both 'glob' and 'ruleset' keys")
        if rule["ruleset"] is not None:
            registry.get_ruleset(rule["ruleset"])  # raises UnknownRulesetError on a typo
        rule = dict(rule)
        for key, value in existing_extras.get(rule["glob"], {}).items():
            rule.setdefault(key, value)
        embedded = rule.get("embedded_prose")
        if embedded:
            registry.get_ruleset(embedded)  # same loud-on-typo guarantee
            if not core_extract.glob_extension_supported(rule["glob"]):
                raise ValueError(
                    f"embedded_prose on {rule['glob']!r}: no extractor for "
                    f"that extension -- supported: "
                    f"{sorted(core_extract.SUPPORTED_EXTENSIONS)}. A binding "
                    f"that can never fire is a gate quietly off.")
        if existing_scope.get(rule["glob"]) != (rule["ruleset"], embedded):
            known_lists, known_checks = _rule_known_lists_and_checks(rule, registry, project_root, config_file)
            if rule.get("packs"):
                rule["packs"] = {lid: ids for lid, ids in rule["packs"].items()
                                  if lid in known_lists}
            if rule.get("disable"):
                rule["disable"] = [c for c in rule["disable"] if c in known_checks]
        if not rule.get("packs"):
            rule.pop("packs", None)
        if not rule.get("disable"):
            rule.pop("disable", None)
        merged.append(rule)

    data["rulesets"] = merged
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def _rule_known_lists_and_checks(rule, registry, project_root, config_file=None):
    module = registry.get_ruleset(rule["ruleset"]) if rule.get("ruleset") else None
    known_lists = (set(effective_term_lists(getattr(module, "TERM_LISTS", {}),
                                             module.RULESET_ID, project_root, config_file))
                   if module else set())
    known_checks = set()
    for ruleset_id in (rule.get("ruleset"), rule.get("embedded_prose")):
        if not ruleset_id:
            continue
        try:
            m = registry.get_ruleset(ruleset_id)
        except Exception:
            continue  # an unknown ruleset id here is caught loudly by save_rules
        if "checks" in m.CAPABILITIES:
            known_checks |= set(m.list_checks())
    return known_lists, known_checks


def orphaned_rule_extras(project_root, registry, config_file=None):
    """Packs and disable entries on a routing rule that no list or check
    the rule actually invokes still recognizes -- dead weight left behind
    when a rule's "ruleset" or "embedded_prose" cell changes but the
    packs and disable entries it carries, written for the ruleset it
    used to name, are never revalidated against the new one. save_rules
    now closes the write side of this gap for its own edits (see its
    docstring); this is the read side, for whatever a config already
    carries -- hand-edited, or written before that fix existed.

    Returns [{"glob":, "packs": {list_id: [pack_id, ...]}, "disable": [check_id, ...]}, ...],
    one entry per rule with anything orphaned, naming only the orphaned
    part -- a pack binding or disable entry that still fits is not
    repeated here. Empty list with no config file, same baseline every
    other knob in this module gives."""
    out = []
    for rule in load_rules(project_root, config_file):
        if not rule.get("ruleset"):
            continue  # an out-of-scope rule (ruleset: null) invokes nothing to check against
        known_lists, known_checks = _rule_known_lists_and_checks(rule, registry, project_root, config_file)
        dead_packs = {lid: ids for lid, ids in (rule.get("packs") or {}).items()
                      if lid not in known_lists and ids}
        dead_disable = [c for c in (rule.get("disable") or []) if c not in known_checks]
        if dead_packs or dead_disable:
            entry = {"glob": rule["glob"]}
            if dead_packs:
                entry["packs"] = dead_packs
            if dead_disable:
                entry["disable"] = dead_disable
            out.append(entry)
    return out


def prune_orphaned_rule_extras(project_root, registry, config_file=None):
    """Remove exactly what orphaned_rule_extras just found, leaving every
    still-valid pack binding and disable entry on every rule untouched.
    Returns what it removed, same shape as orphaned_rule_extras."""
    dead = orphaned_rule_extras(project_root, registry, config_file)
    if not dead:
        return dead
    path = config_file or config_path(project_root)
    with open(path) as f:
        data = json.load(f)
    by_glob = {entry["glob"]: entry for entry in dead}
    for rule in data.get("rulesets", []):
        entry = by_glob.get(rule.get("glob"))
        if not entry:
            continue
        if "packs" in entry and isinstance(rule.get("packs"), dict):
            for list_id in entry["packs"]:
                rule["packs"].pop(list_id, None)
            if not rule["packs"]:
                rule.pop("packs", None)
        if "disable" in entry and isinstance(rule.get("disable"), list):
            rule["disable"] = [c for c in rule["disable"] if c not in entry["disable"]]
            if not rule["disable"]:
                rule.pop("disable", None)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    return dead


def known_extensions(project_root, config_file=None):
    """Literal '*.ext' suffixes named in the resolved rules -- feeds
    bash_write_detect.py's target-extension scope, generalized from the
    hardcoded (.md, .txt, .rst) tuple it used to carry directly. A glob that
    isn't a plain '*.ext' pattern (a directory prefix, a mid-pattern
    wildcard) contributes nothing here -- bash detection only needs the
    extension list, not the full glob logic."""
    exts = set()
    for rule in load_rules(project_root, config_file):
        glob = rule["glob"]
        if glob.startswith("*.") and "/" not in glob and "*" not in glob[2:]:
            exts.add(glob[1:])  # "*.md" -> ".md"
    return exts


def check_config_for_path(project_root, ruleset_id, file_path=None,
                           config_file=None):
    """Per-check overrides for `ruleset_id`, project-wide PLUS whatever the
    routing rule matching `file_path` names in its own "check_config".

    Symmetric with packs and with disable, and asked for on the same
    grounds: "granular and uniform". A threshold is not a property of a
    ruleset, it is a property of a ruleset applied to a KIND of file.
    Measurement made that concrete -- the human band for a formatting
    check is not the same in reference documentation as in a changelog,
    so one number for both is wrong in one of them by construction.

        {"glob": "docs/*.md", "ruleset": "slopwatch",
         "check_config": {"bold_density": {"threshold": 12}}}

    A rule's entry LAYERS over the project-wide one per field, rather than
    replacing the check's whole spec. Replacement would mean naming a
    threshold silently reset that check's action to the ruleset default,
    which is the kind of surprise nobody finds until a write is denied for
    a reason the config does not appear to state.

    Unlike `disable`, this is not union-only: a rule may loosen a
    threshold as well as tighten it. The asymmetry is deliberate.
    Disabling is binary and irreversible-by-a-rule so that "why did this
    not fire?" stays answerable in two places; a threshold is a dial and
    its answer is the same two places whichever way it was turned.
    """
    merged = {check_id: dict(spec) for check_id, spec
               in check_config(project_root, ruleset_id, config_file).items()}
    rule = matching_rule(file_path, project_root, config_file) if file_path else None
    per_rule = (rule or {}).get("check_config") or {}
    if not isinstance(per_rule, dict):
        return merged
    for check_id, override in per_rule.items():
        if not isinstance(override, dict):
            continue
        merged.setdefault(check_id, {}).update(override)
    return merged


def save_rule_check_config(project_root, glob, check_id, spec, config_file=None):
    """Set (or with an empty `spec`, clear) one check's per-rule overrides
    on the routing rule with exactly this glob.

    Addressed by the rule's own glob rather than by path, the same as
    `save_rule_packs`. A path can match only one rule, but naming the rule
    is what makes "which rule did I just change?" answerable without
    re-running the resolver.
    """
    path = config_file or config_path(project_root)
    if not os.path.exists(path):
        raise ValueError("no stopslop.config.json to edit")
    with open(path) as f:
        data = json.load(f)
    # The routing rules live under "rulesets", not "rules" -- load_rules
    # reads data["rulesets"]. Writing to "rules" produced a top-level key
    # nothing reads: the command reported success, the file held the
    # override, and the gate never saw it. That is the dead-key failure
    # this module's own KNOWN_TOP_LEVEL_KEYS exists to catch, reproduced
    # by a writer that guessed the name instead of reading the reader.
    rules = data.get("rulesets") or []
    for rule in rules:
        if rule.get("glob") != glob:
            continue
        existing = dict(rule.get("check_config") or {})
        if spec:
            existing[check_id] = spec
        else:
            existing.pop(check_id, None)
        if existing:
            rule["check_config"] = existing
        else:
            rule.pop("check_config", None)
        data["rulesets"] = rules
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
        return rule
    raise ValueError(f"no routing rule with glob {glob!r}")
