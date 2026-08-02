"""Path -> ruleset resolution.

A project's `stopslop.config.json` (repo root, sibling to stopslop.py) maps
glob patterns to a ruleset id, first-match-wins -- the same override-list
shape ESLint's `overrides` uses. Lives at the repo root rather than under
`.claude/` on purpose: `.claude/settings.local.json` is per-clone machine
wiring (hook command paths templated for one checkout, gitignored); this is
project-level policy the CLI and MCP server need with no live Claude Code
session at all, closer to `.eslintrc` or `pyproject.toml`.

With no config file present, DEFAULT_RULES reproduces exactly what
pretool_hook.py's `in_scope()` did before rulesets existed: STE100 on
.md/.txt/.rst, `.claude/` out of scope entirely. That equivalence is a
required invariant (see core/test_config.py) -- a ruleset existing in the
code registry must never change behavior for a clone with no config file.

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

DEFAULT_RULES = [
    {"glob": ".claude/*", "ruleset": None},
    {"glob": "*.md", "ruleset": "ste100"},
    {"glob": "*.txt", "ruleset": "ste100"},
    {"glob": "*.rst", "ruleset": "ste100"},
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


def enabled_glossary_packs(project_root, ruleset_id, config_file=None):
    """Which named vocabulary packs are active for `ruleset_id`, per
    stopslop.config.json's "glossary_packs" key: {"<ruleset_id>":
    ["<pack_id>", ...]}. Empty with no config file, and empty for a
    ruleset_id the key doesn't mention -- a pack existing in code must
    never change behavior for an unconfigured clone, the same invariant
    DEFAULT_RULES already guarantees for ruleset routing. Lives in this
    module, not in a ruleset package, so stopslop.config.json stays the
    one file that knows the whole project's configuration shape."""
    path = config_file or config_path(project_root)
    if not os.path.exists(path):
        return []
    with open(path) as f:
        data = json.load(f)
    return data.get("glossary_packs", {}).get(ruleset_id, [])


def save_glossary_packs(project_root, ruleset_id, pack_ids, config_file=None):
    """Write which packs are enabled for `ruleset_id`, preserving every
    other top-level key already in the file (routing rules, another
    ruleset's own pack list) -- a blind overwrite here would be the exact
    settings.local.json-clobber bug this project already found and fixed
    once in stopslop.py's own init --force."""
    path = config_file or config_path(project_root)
    data = {}
    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
    data.setdefault("glossary_packs", {})[ruleset_id] = pack_ids
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


def resolve_ruleset_id(file_path, project_root, config_file=None):
    """The bare ruleset id a path resolves to, or None if out of scope
    (either no rule matched, or the matching rule's ruleset is explicitly
    null). Does not touch the ruleset registry at all -- split out from
    resolve_ruleset() so callers that only need the id (e.g.
    bash_write_detect's scope check) don't need a live registry, and so this
    half stays testable with zero rulesets registered anywhere."""
    rel = _relative_posix_path(file_path, project_root)
    if rel is None:
        return None
    for rule in load_rules(project_root, config_file):
        if fnmatch.fnmatch(rel, rule["glob"]):
            return rule["ruleset"]
    return None


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
    level key already in the file (e.g. "glossary_packs") -- a blind
    overwrite here would be the exact settings.local.json-clobber bug this
    project already found and fixed once in stopslop.py's own init
    --force, now with a second config file it could happen to again."""
    for rule in rules:
        if "glob" not in rule or "ruleset" not in rule:
            raise ValueError(f"rule {rule!r} needs both 'glob' and 'ruleset' keys")
        if rule["ruleset"] is not None:
            registry.get_ruleset(rule["ruleset"])  # raises UnknownRulesetError on a typo
    path = config_file or config_path(project_root)
    data = {}
    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
    data["rulesets"] = rules
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
