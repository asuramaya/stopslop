"""Bulk-scan an existing tree of files against one or more rulesets.

Every other check in this project looks at one file, or one string, at a
time -- `lint_and_gate` on a single live write, `stopslop.py lint --file`
on one path. That is enough for the live gate, which only ever sees one
write at a time, but it leaves a real gap for a project adopting stopslop
onto a codebase that already exists: there was no way to see what the
current tree would already flag before ever touching a live PreToolUse
write. scan_tree() is that missing piece -- walk a path, resolve (or
force) a ruleset per file, lint every one, and return one aggregate
report, reusing the exact lint_and_gate/blocking_semantic_flags functions
the live gate and the CLI's own `lint` command already call so a scan's
verdict never drifts from what a real edit would actually do.
"""
import fnmatch
import os

from core import config as core_config

SKIP_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", ".idea", ".vscode",
    ".cache", "dist", "build", ".tox", "site-packages",
}


def _iter_files(paths, glob_pattern):
    # Only the explicit names above are non-negotiable (real version-control/
    # tooling internals, never real content). Anything else -- including a
    # dot-dir -- stays walkable, so a custom stopslop.config.json rule (e.g.
    # ".github/*.md") stays the sole authority over what's in scope instead
    # of being silently overridden by a blanket "skip every dot-dir" guess.
    for p in paths:
        if os.path.isfile(p):
            yield p
            continue
        for root, dirs, files in os.walk(p):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for name in sorted(files):
                if glob_pattern and not fnmatch.fnmatch(name, glob_pattern):
                    continue
                yield os.path.join(root, name)


def scan_tree(paths, project_root, registry, ruleset_id=None, glob_pattern=None, config_file=None):
    """Lint every in-scope file under `paths` (a list of file or directory
    paths).

    ruleset_id=None (default) resolves each file's ruleset the same way a
    live write would (core.config.resolve_ruleset_id) and skips a file that
    doesn't resolve to anything -- exactly what the live gate would already
    ignore. This answers "what would the gate flag across the whole tree,
    right now, under the current config."

    ruleset_id="slopwatch" (etc.) forces every matched file through that one
    ruleset regardless of config routing -- this is what lets a project
    test a ruleset against files it is not wired up to lint yet (e.g.
    slopwatch against an existing docs/ tree before adding a routing rule
    for it). `glob_pattern` narrows which filenames are included in this
    mode (default: every regular file); it is ignored in the resolve-from-
    config mode, since the config's own globs already narrow file selection
    there.

    Returns {"scanned", "skipped_out_of_scope", "skipped_unreadable",
    "results": [{"path", "ruleset", "would_block", "blocking_flags",
    "all_semantic_flags", "mechanical_flags"}, ...]}.
    """
    forced = registry.get_ruleset(ruleset_id) if ruleset_id else None
    results = []
    skipped_out_of_scope = 0
    skipped_unreadable = 0

    for path in _iter_files(paths, glob_pattern if forced else None):
        if forced:
            ruleset = forced
        else:
            resolved_id = core_config.resolve_ruleset_id(path, project_root, config_file)
            if resolved_id is None:
                skipped_out_of_scope += 1
                continue
            ruleset = registry.get_ruleset(resolved_id)

        try:
            with open(path, encoding="utf-8") as f:
                text = f.read()
        except (UnicodeDecodeError, OSError):
            skipped_unreadable += 1
            continue

        if not text.strip():
            continue

        result = ruleset.lint_and_gate(text, context=None, file_path=path)
        blocking = ruleset.blocking_semantic_flags(result["semantic_flags"])
        results.append({
            "path": path,
            "ruleset": ruleset.RULESET_ID,
            "would_block": bool(blocking),
            "blocking_flags": blocking,
            "all_semantic_flags": result["semantic_flags"],
            "mechanical_flags": result["mechanical_violations"],
            # Whitespace-split, the same crude count every metric in
            # evalab uses, so a rate computed here and a rate computed
            # there are the same number and not two dialects of one.
            "words": len(text.split()),
        })

    return {
        "scanned": len(results),
        "skipped_out_of_scope": skipped_out_of_scope,
        "skipped_unreadable": skipped_unreadable,
        "results": results,
    }


def check_activity(report, ruleset):
    """Which of a ruleset's checks the corpus in `report` actually fires.

    `scan_tree` answers "what did this tree trip". This answers the
    question no tool in this category can ask: what did it NOT trip. A
    check catalogued against 2023-24 output may simply not describe a
    current model any more, and a check that never fires is invisible
    precisely because absence produces no output.

    Returns {check_id: {"hits", "files", "per_1k"}} for EVERY check the
    ruleset has, zeros included, plus the corpus totals.
    """
    every = sorted(ruleset.list_checks())
    activity = {check_id: {"hits": 0, "files": 0, "per_1k": 0.0}
                 for check_id in every}
    words = 0
    for result in report["results"]:
        if result["ruleset"] != ruleset.RULESET_ID:
            continue
        words += result.get("words", 0)
        seen = set()
        for flag in result["all_semantic_flags"]:
            kind = flag.get("kind")
            if kind not in activity:
                continue
            activity[kind]["hits"] += 1
            seen.add(kind)
        for kind in seen:
            activity[kind]["files"] += 1
    for entry in activity.values():
        entry["per_1k"] = round(entry["hits"] / words * 1000, 2) if words else 0.0
    total_hits = sum(e["hits"] for e in activity.values())
    return {"activity": activity, "words": words, "total_hits": total_hits,
             "documents": sum(1 for r in report["results"]
                               if r["ruleset"] == ruleset.RULESET_ID)}


# A check earns the word "tell" by firing more on generated prose than on
# human prose. These bounds split that into four honest verdicts.
DISCRIMINATES_AT = 2.0
BACKWARDS_AT = 0.5


def compare_activity(measured, control):
    """Per-check discrimination between two corpora.

    `check_activity` answers "does this check ever fire". This answers
    the question that decides whether a check is a TELL at all: does it
    fire more on the text you are trying to catch than on the text you
    are trying to sound like?

    A check that fires equally on both is not detecting a machine. It is
    encoding a style preference, and enforcing it moves prose away from
    the human distribution rather than toward it. A check that fires MORE
    on the control is worse than useless: it actively penalises the thing
    the writer is aiming at.

    Verdicts: "discriminates", "no signal", "backwards", "silent".
    """
    rows = {}
    for check_id, entry in measured["activity"].items():
        gen = entry["per_1k"]
        hum = control["activity"].get(check_id, {}).get("per_1k", 0.0)
        if not gen and not hum:
            verdict, ratio = "silent", None
        elif not hum:
            verdict, ratio = "discriminates", None
        else:
            ratio = gen / hum
            if ratio >= DISCRIMINATES_AT:
                verdict = "discriminates"
            elif ratio <= BACKWARDS_AT:
                verdict = "backwards"
            else:
                verdict = "no signal"
        rows[check_id] = {"per_1k": gen, "control_per_1k": hum,
                           "ratio": ratio, "verdict": verdict}
    return rows


def consensus_verdicts(per_control):
    """One verdict per check across SEVERAL control corpora.

    Two controls do not make a genre confound disappear; they make it
    visible. This project nearly cut a good check on one corpus alone:
    `colon_reveal` scored 1.0x against code documentation -- no signal,
    apparently a style preference -- and 25.8x against pre-2022
    Wikipedia prose. Code documentation is full of colons whatever wrote
    it, and only a second genre could show that.

    So the rule is unanimity, and it is deliberately hard to condemn a
    check with:

      "discriminates" -- every control agrees it fires more on the
          measured text.
      "backwards" -- every control agrees it fires more on the control.
          This is the only verdict that justifies cutting a check.
      "silent" -- it fired nowhere at all.
      "disputed" -- the controls disagree. Not a result. It means the
          genres differ on this check and neither one settles it.

    With a single control, "disputed" cannot occur and every verdict is
    provisional. That is not a flaw in the arithmetic; it is what one
    corpus is worth.
    """
    if not per_control:
        return {}
    consensus = {}
    for check_id in per_control[0]:
        verdicts = {rows.get(check_id, {}).get("verdict") for rows in per_control}
        verdicts.discard(None)
        if verdicts == {"silent"}:
            consensus[check_id] = "silent"
        elif verdicts == {"discriminates"}:
            consensus[check_id] = "discriminates"
        elif verdicts == {"backwards"}:
            consensus[check_id] = "backwards"
        elif verdicts == {"no signal"}:
            consensus[check_id] = "no signal"
        else:
            consensus[check_id] = "disputed"
    return consensus
