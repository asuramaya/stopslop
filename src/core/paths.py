"""Project-root discovery that works from any depth inside src/
(src/, src/core/, src/rulesets/<id>/, ...).

Before the pluggable-ruleset refactor, every orchestrator script computed
its own project root as a literal `os.path.dirname(os.path.abspath(__file__))`
chain of a fixed length -- fragile in the same way the earlier hardcoded
PROJECT_ROOT string was fragile (found and fixed earlier in this project's
history): it silently breaks the moment a file moves to a different nesting
depth, which the refactor that introduced rulesets/<id>/ packages did to
several files at once. This walks up from a given file until it finds
stopslop.py, the one stable landmark at the repo root, instead of hardcoding
a dirname() count anywhere.
"""
import os

_MARKER = "stopslop.py"


def find_project_root(start_file):
    d = os.path.dirname(os.path.abspath(start_file))
    while True:
        if os.path.exists(os.path.join(d, _MARKER)):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            raise RuntimeError(
                f"could not find project root (looked for {_MARKER!r} while "
                f"walking up from {start_file!r})")
        d = parent
