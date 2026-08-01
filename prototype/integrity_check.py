#!/usr/bin/env python3
"""Cheap drift detection for the gate's own trust anchors: enforcement data
(ste100_dictionary.json) and the gate code itself (ste100_lint.py,
pretool_hook.py, bash_write_detect.py, build_dictionary.py). Responds to a
real gap found this session: the design doc's own section 10.3 mitigation
assumes these files are under version control, where an unexpected change
shows as a diff -- but this project has no git repository, so that
assumption doesn't hold here at all.

Not access control and not tamper prevention -- a hash registry an agent can
also edit doesn't stop a determined rewrite. What it does do: make a change
to these specific files VISIBLE at the next session start, even if nobody
was watching when it happened, which is strictly better than the current
alternative (no record at all). Real access control needs the git repository
this project doesn't have; recommended, not built here.

Baseline model: the registry stores each tracked file's hash as of the last
SessionStart. Every SessionStart compares current hashes against that
baseline, reports any mismatch as a warning, THEN overwrites the registry
with the current hashes. A legitimate edit made during a session surfaces as
a one-time "changed since last session" notice at the NEXT session start --
informational, not a block, matching this project's existing division of
labor (the write-gate blocks bad content; this just makes drift visible).
"""
import hashlib
import json
import os

PROJECT_ROOT = "/home/asuramaya/code/stopslop/"
PROTOTYPE_DIR = os.path.join(PROJECT_ROOT, "prototype")
REGISTRY_PATH = os.path.join(PROJECT_ROOT, ".claude", "ste100-integrity.json")

TRACKED_FILES = [
    os.path.join(PROTOTYPE_DIR, "ste100_dictionary.json"),
    os.path.join(PROTOTYPE_DIR, "ste100-project-terms.json"),
    os.path.join(PROTOTYPE_DIR, "ste100_lint.py"),
    os.path.join(PROTOTYPE_DIR, "pretool_hook.py"),
    os.path.join(PROTOTYPE_DIR, "bash_write_detect.py"),
    os.path.join(PROTOTYPE_DIR, "build_dictionary.py"),
]


def _hash_file(path):
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def check_and_update():
    """Returns a list of human-readable warning strings (empty if this is
    the first run, or if nothing tracked has changed since the last one)."""
    current = {path: _hash_file(path) for path in TRACKED_FILES}

    warnings = []
    if os.path.exists(REGISTRY_PATH):
        try:
            with open(REGISTRY_PATH) as f:
                previous = json.load(f)
        except (OSError, json.JSONDecodeError):
            previous = {}
        for path, current_hash in current.items():
            name = os.path.basename(path)
            prev_hash = previous.get(path)
            if prev_hash is None:
                continue  # newly tracked file, nothing to compare against yet
            if current_hash is None:
                warnings.append(f"{name}: tracked file is missing (was present last session)")
            elif current_hash != prev_hash:
                warnings.append(f"{name}: changed since last session start "
                                 f"({prev_hash[:12]}... -> {current_hash[:12]}...)")

    try:
        os.makedirs(os.path.dirname(REGISTRY_PATH), exist_ok=True)
        with open(REGISTRY_PATH, "w") as f:
            json.dump(current, f, indent=2, sort_keys=True)
            f.write("\n")
    except OSError:
        pass  # integrity tracking must never break session start

    return warnings
