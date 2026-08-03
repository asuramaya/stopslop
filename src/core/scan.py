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
        })

    return {
        "scanned": len(results),
        "skipped_out_of_scope": skipped_out_of_scope,
        "skipped_unreadable": skipped_unreadable,
        "results": results,
    }
