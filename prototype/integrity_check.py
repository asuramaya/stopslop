#!/usr/bin/env python3
"""Cheap drift detection for the gate's own trust anchors: core gate code
(pretool_hook.py, bash_write_detect.py, everything under core/) plus each
registered ruleset's own TRACKED_FILES (enforcement data and rule logic,
e.g. rulesets/ste100/dictionary.json).

This project does have a git repository (since its first commit) -- an
earlier version of this docstring claimed otherwise, which was already
false the moment it was written; corrected during an earlier adversarial
review. Git diffing these files is still a real mitigation, but it needs
someone to proactively run it: a change made mid-session, before it's ever
staged or committed, is invisible to `git diff` until somebody thinks to
look, and a change that IS committed is still only visible to a reviewer
who actually opens that diff. This check adds an automatic, passive layer
on top: it runs unprompted at every SessionStart and surfaces a warning
whether or not the change was ever committed, staged, or reviewed by anyone.

Not access control and not tamper prevention -- a hash registry an agent can
also edit doesn't stop a determined rewrite, and neither does git history an
agent can also rewrite. What it does do: make a change to these specific
files VISIBLE at the next session start, even if nobody was watching when it
happened and nobody thought to check the diff, which is strictly better than
relying on someone remembering to look.

Baseline model: the registry stores each tracked file's hash as of the last
SessionStart, namespaced by "_core" and each ruleset id (so two rulesets'
same-named files, e.g. two lint.py, never collide). Every SessionStart
compares current hashes against that baseline, reports any mismatch as a
warning, THEN overwrites the registry with the current hashes. A legitimate
edit made during a session surfaces as a one-time "changed since last
session" notice at the NEXT session start -- informational, not a block,
matching this project's existing division of labor (the write-gate blocks
bad content; this just makes drift visible).
"""
import hashlib
import json
import os

from core import paths
import rulesets

_LEGACY_REGISTRY_NAME = "ste100-integrity.json"
_REGISTRY_NAME = "stopslop-integrity.json"

# Relative to prototype/ (this file's own directory). Matches the pre-
# refactor scope exactly (the live write-time enforcement path), plus the
# core/ modules that used to be part of pretool_hook.py/ste100_lint.py
# directly and were already tracked implicitly as part of those files.
CORE_TRACKED_FILES = ["pretool_hook.py", "bash_write_detect.py",
                       "core/blocks.py", "core/flags.py", "core/config.py",
                       "core/history.py", "core/paths.py"]


def _registry_path(project_root):
    return os.path.join(project_root, ".claude", _REGISTRY_NAME)


def _legacy_registry_path(project_root):
    return os.path.join(project_root, ".claude", _LEGACY_REGISTRY_NAME)


def _hash_file(path):
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def _current_hashes(project_root):
    """{"_core": {relpath: hash}, "<ruleset_id>": {relpath: hash}, ...} for
    every tracked file -- core files resolved against prototype/ (this
    file's own directory), each ruleset's files resolved against that
    ruleset module's own package directory."""
    prototype_dir = os.path.dirname(os.path.abspath(__file__))
    current = {"_core": {f: _hash_file(os.path.join(prototype_dir, f))
                          for f in CORE_TRACKED_FILES}}
    for ruleset in rulesets.list_rulesets():
        ruleset_dir = os.path.dirname(os.path.abspath(ruleset.__file__))
        tracked = getattr(ruleset, "TRACKED_FILES", [])
        current[ruleset.RULESET_ID] = {f: _hash_file(os.path.join(ruleset_dir, f))
                                        for f in tracked}
    return current


def _migrate_legacy_registry(project_root):
    """One-time: rename the pre-refactor ste100-only registry file so the
    new namespaced baseline has something to migrate from, rather than
    starting cold. Never breaks session start if it fails.

    The old file's content (a flat {absolute_path: hash} map) doesn't match
    the new {"_core": {...}, "<ruleset_id>": {...}} shape at all --
    deliberately not translated key-by-key. Every lookup against it in
    check_and_update() below simply misses and is treated as "newly
    tracked, nothing to compare against yet," so the first session after
    this migration silently re-establishes a full baseline with no false
    "everything changed" warning spam."""
    new_path = _registry_path(project_root)
    old_path = _legacy_registry_path(project_root)
    if os.path.exists(new_path) or not os.path.exists(old_path):
        return
    try:
        os.rename(old_path, new_path)
    except OSError:
        pass


def check_and_update():
    """Returns a list of human-readable warning strings (empty if this is
    the first run, or if nothing tracked has changed since the last one)."""
    project_root = paths.find_project_root(__file__)
    _migrate_legacy_registry(project_root)
    registry_path = _registry_path(project_root)
    current = _current_hashes(project_root)

    warnings = []
    if os.path.exists(registry_path):
        try:
            with open(registry_path) as f:
                previous = json.load(f)
        except (OSError, json.JSONDecodeError):
            previous = {}
        for group, files in current.items():
            prev_group = previous.get(group, {}) if isinstance(previous, dict) else {}
            for name, current_hash in files.items():
                prev_hash = prev_group.get(name) if isinstance(prev_group, dict) else None
                if prev_hash is None:
                    continue  # newly tracked file, nothing to compare against yet
                label = name if group == "_core" else f"{group}/{name}"
                if current_hash is None:
                    warnings.append(f"{label}: tracked file is missing (was present last session)")
                elif current_hash != prev_hash:
                    warnings.append(f"{label}: changed since last session start "
                                     f"({prev_hash[:12]}... -> {current_hash[:12]}...)")

    try:
        os.makedirs(os.path.dirname(registry_path), exist_ok=True)
        with open(registry_path, "w") as f:
            json.dump(current, f, indent=2, sort_keys=True)
            f.write("\n")
    except OSError:
        pass  # integrity tracking must never break session start

    return warnings
