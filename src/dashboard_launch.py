#!/usr/bin/env python3
"""Singleton launcher for webui/app.py -- lets mcp_server.py auto-start
the dashboard on load without every concurrent session (or harness)
racing to spawn its own copy and burn CPU on N idle server processes.

Two guards, not one:

- A liveness probe (`is_alive`) answers "is a dashboard already serving
  this port" by hitting the app's own `/health` endpoint, not just
  checking whether the TCP port is open -- an unrelated process holding
  the port reads as absent rather than as our dashboard, and a crashed
  dashboard reads as absent rather than as alive forever the way a stale
  pidfile would.
- An flock on `.claude/stopslop-dashboard.lock` closes the race the probe
  alone can't: two sessions loading MCP in the same instant can both see
  "not alive" before either has started listening. Only the lock's winner
  spawns; every loser returns immediately without spawning a second copy.
  The winner holds the lock until the child is confirmed alive (or times
  out), so a session that blocks briefly waiting for the lock finds a
  live dashboard on the other side, not an empty invitation to spawn one
  itself.

The spawned process is detached (`start_new_session` / `DETACHED_PROCESS`)
so it outlives whichever MCP server process happened to win the race --
otherwise the dashboard would die the moment that one session's Claude
Code window closed, and the next session to load MCP would just restart
the churn instead of finding a stable, shared server.

POSIX (fcntl.flock) and Windows (msvcrt.locking) both implemented -- this
module has no import-time dependency on mcp or fastapi, so it stays
importable and unit-testable under the stdlib-only suite.
"""
import importlib.util
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

from core import paths

DASHBOARD_PORT = 8501
_LOCK_NAME = "stopslop-dashboard.lock"
_LOG_NAME = "stopslop-dashboard.log"
_SPAWN_TIMEOUT_SECONDS = 10
_POLL_INTERVAL_SECONDS = 0.25


def dashboard_url(port=DASHBOARD_PORT):
    return f"http://localhost:{port}"


def venv_python_path(repo_root):
    """Where `stopslop.py dashboard`'s own venv interpreter lives -- unlike
    the MCP path (always launched via mcp_launch.py's execv into the venv,
    so `sys.executable` already IS this), the CLI can be invoked by plain
    system python3, so it has to resolve the venv explicitly. `bin/python3`
    vs `Scripts/python.exe` is the one real platform fork here; `-m
    uvicorn` below is what avoids a second one (guessing whether the
    uvicorn entry point is a `bin/uvicorn` script, a `Scripts/
    uvicorn.exe`, or something else pip decided to generate)."""
    if os.name == "nt":
        return os.path.join(repo_root, ".venv", "Scripts", "python.exe")
    return os.path.join(repo_root, ".venv", "bin", "python3")


def uvicorn_argv(python_exe, src_dir, port):
    """`--app-dir` puts `src_dir` on uvicorn's own import path before it
    resolves `webui.app:app` by dotted name -- the same role a script's
    own directory being auto-added to sys.path played for `streamlit run
    dashboard.py` (this project's previous dashboard), just spelled as an
    explicit flag instead of an implicit one, since uvicorn imports a
    module rather than running a script."""
    return [python_exe, "-m", "uvicorn", "webui.app:app",
            "--app-dir", src_dir, "--port", str(port), "--host", "127.0.0.1"]


def is_alive(port=DASHBOARD_PORT, timeout=0.5):
    """True if something at 127.0.0.1:port answers as a live instance of
    this app. HTTPError (a 404, say, from an unrelated service on that
    port) is raised before the `with` block's __enter__ runs, so it's
    caught and closed explicitly rather than falling through to the
    generic OSError branch -- letting it fall through would leak the
    response's socket instead of releasing it."""
    try:
        with urllib.request.urlopen(
                f"http://127.0.0.1:{port}/health", timeout=timeout) as resp:
            return resp.status == 200
    except urllib.error.HTTPError as exc:
        exc.close()
        return False
    except (OSError, ValueError):
        return False


def _lock_path(project_root):
    return os.path.join(project_root, ".claude", _LOCK_NAME)


def _log_path(project_root):
    return os.path.join(project_root, ".claude", _LOG_NAME)


def _log(project_root, message):
    try:
        with open(_log_path(project_root), "a") as f:
            f.write(f"{message}\n")
    except OSError as ignored:
        pass


def _acquire_lock(fd):
    """Try to take an exclusive, non-blocking lock on fd. True if won --
    flock associates the lock with the open file description, not the
    process, so two independent os.open() calls on the same path (even
    from the same process, which is what the tests exploit) behave as
    genuinely separate lock holders, same as two different processes
    would."""
    if os.name == "nt":
        import msvcrt
        try:
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            return True
        except OSError:
            return False
    import fcntl
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except OSError:
        return False


def _release_lock(fd):
    if os.name == "nt":
        import msvcrt
        try:
            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        except OSError as ignored:
            pass
    else:
        import fcntl
        fcntl.flock(fd, fcntl.LOCK_UN)


def _spawn_detached(python_exe, port, log_path, project_root):
    kwargs = {}
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True
    src_dir = os.path.join(project_root, "src")
    log_fh = open(log_path, "a")
    try:
        subprocess.Popen(
            uvicorn_argv(python_exe, src_dir, port),
            stdin=subprocess.DEVNULL, stdout=log_fh, stderr=subprocess.STDOUT,
            cwd=project_root, close_fds=True, **kwargs,
        )
    finally:
        log_fh.close()


def _wait_until_alive(port, timeout=_SPAWN_TIMEOUT_SECONDS, interval=_POLL_INTERVAL_SECONDS):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if is_alive(port):
            return True
        time.sleep(interval)
    return is_alive(port)


def ensure_running(project_root=None, port=DASHBOARD_PORT, python_exe=None):
    """Start the dashboard if nothing is already serving `port`. Safe to
    call from every session's MCP server on startup: at most one caller,
    across however many concurrent processes call this at once, actually
    spawns it -- see the module docstring for the lock+probe mechanism
    that guarantees it.

    Best-effort and silent on failure (missing fastapi, a port some
    other process holds, a spawn that never comes up healthy) -- logged
    to .claude/stopslop-dashboard.log rather than raised, because the
    dashboard is a convenience surface and must never be able to take an
    MCP server's startup down with it."""
    project_root = project_root or paths.find_project_root(__file__)
    python_exe = python_exe or sys.executable
    try:
        if is_alive(port):
            return
        if importlib.util.find_spec("fastapi") is None:
            _log(project_root, "dashboard auto-start skipped: fastapi not "
                                "installed in this interpreter")
            return
        lock_path = _lock_path(project_root)
        os.makedirs(os.path.dirname(lock_path), exist_ok=True)
        fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o644)
        try:
            if not _acquire_lock(fd):
                return  # another session is already handling this
            if is_alive(port):
                return  # the lock's winner finished between our two probes
            _spawn_detached(python_exe, port, _log_path(project_root), project_root)
            if not _wait_until_alive(port):
                _log(project_root,
                     f"dashboard did not come up healthy on port {port} within "
                     f"{_SPAWN_TIMEOUT_SECONDS}s -- see this file for uvicorn's own output")
        finally:
            _release_lock(fd)
            os.close(fd)
    except Exception as exc:
        _log(project_root, f"dashboard auto-start failed: {exc!r}")
