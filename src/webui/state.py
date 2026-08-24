"""Server-side snapshot/undo for stopslop.config.json -- the mutate-then-
refetch replacement for dashboard.py's old _snapshot()/_undo_bar() pair.

Every page here is rendered fresh from disk on every request; nothing
mirrors a value between requests the way a keyed Streamlit widget's
session state did. That's what makes this simpler than the version it
replaces: restoring the config file IS restoring what the next render
shows, with no equivalent of the old param::/pack::/checks_editor::/
ruledisable:: session-state-key-clearing dance needed alongside it --
there is no stale client-side mirror left to clear.

One undo slot, matching the old UI's own "last change" semantics (not a
history stack) -- stored in .claude/webui-undo.json, next to the other
per-clone runtime state this project already keeps there
(stopslop-history.log, stopslop-dashboard.lock).
"""
import json
import os

from core import config as core_config

_UNDO_NAME = "webui-undo.json"


def _undo_path(project_root):
    return os.path.join(project_root, ".claude", _UNDO_NAME)


def snapshot(project_root, label):
    """Remember stopslop.config.json exactly as it is, under a human
    label. Call this BEFORE the write it's protecting against."""
    path = core_config.config_path(project_root)
    blob = None
    if os.path.exists(path):
        with open(path) as f:
            blob = f.read()
    entry = {"label": label, "blob": blob, "path": path}
    os.makedirs(os.path.dirname(_undo_path(project_root)), exist_ok=True)
    with open(_undo_path(project_root), "w") as f:
        json.dump(entry, f)


def last(project_root):
    """The current undo entry ({"label", "blob", "path"}), or None if
    there is nothing to undo -- what the UI shows as "Last change: ..."."""
    p = _undo_path(project_root)
    if not os.path.exists(p):
        return None
    try:
        with open(p) as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def undo(project_root):
    """Restore the last snapshot and clear the slot. Returns True if
    something was restored, False if there was nothing to undo."""
    entry = last(project_root)
    if entry is None:
        return False
    if entry["blob"] is None:
        if os.path.exists(entry["path"]):
            os.unlink(entry["path"])
    else:
        with open(entry["path"], "w") as f:
            f.write(entry["blob"])
    os.unlink(_undo_path(project_root))
    return True
