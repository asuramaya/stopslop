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
this is now a deliberate, tested widening of the baseline default, not a
drift: `*.py` routes to codewatch (this project's own primary language),
and the repo-root `README.md` -- prose meant to read like a person wrote
it, exactly the AI-polish target slopwatch protects against -- routes to
slopwatch. ste100 keeps every other `.md`/`.txt`/`.rst` file, unchanged;
`README.md` matches before the general `*.md` rule since first-match-wins
checks rules in order, top to bottom.

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

# Free text (CLI stdin, an MCP lint_text call, the dashboard playground) has
# no real file to route on, so every entry point treats it as if written to
# this name at the repo root -- reusing the one real config-driven resolver
# instead of each growing its own "default ruleset" fallback that could drift
# from it. Defined here, next to the resolver, because stopslop.py and
# mcp_server.py each used to carry their own copy of the literal.
SYNTHETIC_TEXT_NAME = "__stdin__.md"

DEFAULT_RULES = [
    {"glob": ".claude/*", "ruleset": None},
    {"glob": "README.md", "ruleset": "slopwatch"},
    {"glob": "*.md", "ruleset": "ste100"},
    {"glob": "*.txt", "ruleset": "ste100"},
    {"glob": "*.rst", "ruleset": "ste100"},
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
    a project deliberately switched off."""
    disabled = set(disabled_checks(project_root, ruleset_id, config_file))
    rule = matching_rule(file_path, project_root, config_file) if file_path else None
    if rule and rule.get("ruleset") == ruleset_id:
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


def ruleset_options(project_root, ruleset_id, config_file=None):
    """Per-ruleset tunable option overrides (e.g. slopwatch's block-flag-
    count threshold), per stopslop.config.json's "options" key:
    {"<ruleset_id>": {"<option_name>": <value>}}. Empty with no config
    file, or no entry for this ruleset -- a ruleset's own hardcoded
    defaults keep governing an unconfigured clone, the same invariant
    every other knob in this file gives."""
    path = config_file or config_path(project_root)
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        data = json.load(f)
    return data.get("options", {}).get(ruleset_id, {})


def save_ruleset_options(project_root, ruleset_id, options, config_file=None):
    """Write tunable option overrides for `ruleset_id`, preserving every
    other top-level key already in the file -- same clobber-avoidance
    shape as the other save_* helpers here."""
    path = config_file or config_path(project_root)
    data = {}
    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
    data.setdefault("options", {})[ruleset_id] = options
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
    unnoticed)."""
    from core import extract as core_extract

    existing_extras = {}
    path = config_file or config_path(project_root)
    data = {}
    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
        for rule in data.get("rulesets", []):
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
        if not rule.get("packs"):
            rule.pop("packs", None)
        embedded = rule.get("embedded_prose")
        if embedded:
            registry.get_ruleset(embedded)  # same loud-on-typo guarantee
            if not core_extract.glob_extension_supported(rule["glob"]):
                raise ValueError(
                    f"embedded_prose on {rule['glob']!r}: no extractor for "
                    f"that extension -- supported: "
                    f"{sorted(core_extract.SUPPORTED_EXTENSIONS)}. A binding "
                    f"that can never fire is a gate quietly off.")
        merged.append(rule)

    data["rulesets"] = merged
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


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
