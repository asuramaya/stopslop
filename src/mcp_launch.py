#!/usr/bin/env python3
"""Launcher for mcp_server.py, run via system python3 (guaranteed present,
unlike the venv). Checks the venv exists before handing off to it, so a
missing setup step fails with a clear, actionable stderr message instead
of a bare "No such file or directory" from the OS trying to exec a path
that doesn't exist -- confirmed live: pointing .mcp.json directly at
.venv/bin/python3 with no venv set up produces exactly that opaque error,
with no hint of what to do about it or where mcp_server.py's own
dependency is documented.

.mcp.json invokes this file, not mcp_server.py directly, for exactly this
reason.
"""
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENV_PYTHON = os.path.join(REPO_ROOT, ".venv", "bin", "python3")
SERVER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mcp_server.py")

if not os.path.exists(VENV_PYTHON):
    print(
        "stopslop MCP server: no virtual environment at .venv -- it needs one, "
        "unlike the gate itself, which needs nothing installed. Set it up, "
        "then restart this session:\n"
        f"  python3 -m venv {os.path.join(REPO_ROOT, '.venv')}\n"
        f"  {VENV_PYTHON} -m pip install -r {os.path.join(REPO_ROOT, 'requirements.txt')}",
        file=sys.stderr,
    )
    sys.exit(1)

os.execv(VENV_PYTHON, [VENV_PYTHON, SERVER])
