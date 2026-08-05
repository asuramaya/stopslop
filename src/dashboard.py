#!/usr/bin/env python3
"""Local live dashboard for stopslop, run with `stopslop.py dashboard`.

Two destinations, not five -- Watch and Configure, chosen because that's
the actual split in how a human uses this, not how stopslop's own files
happen to be laid out on disk:

- Watch is passive: what did the gate just do, and why. Denials pulled
  out into their own callout, since a deny is the one event a human
  actually wants explained -- everything else is routine.
- Configure is deliberate: pick a path, and every control over what the
  gate does to it is on one screen -- see configure.py's own docstring
  for the layout. There is one path box on the page and no ruleset
  dropdown anywhere, because a path already implies its ruleset and two
  controls for one idea can disagree.

A status footer sits below both pages, outside the navigation, so the
same ambient "is everything okay" line is there regardless of which page
is open.

Not a second gate, not a second config store -- the same distinction the
MCP server's own docstring already draws for itself. This reads and
writes the exact files the hook, the CLI, and an agent editing
stopslop.config.json directly all already use: `.claude/stopslop-
history.log` for activity, `stopslop.config.json` for routing, and each
ruleset's own glossary file for terms. An edit made here is visible to
the next gate call immediately (config is re-read fresh every call, see
core/config.py), and an edit an agent makes directly to those same files
is visible here on the next auto-refresh -- one shared source of truth,
not two that can drift apart.

Every write goes through the same functions the CLI and hook already
call (core.config.save_rules, a ruleset's own register_term/
unregister_term) rather than a raw file write, so validation never gets
a second, divergent copy: an unknown ruleset id or an already-forbidden
word gets refused here exactly as loudly as it would from the CLI.

Run with:
    stopslop.py dashboard
or directly:
    .venv/bin/streamlit run src/dashboard.py
"""
import os
import sys
import time

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import configure as _configure
import rulesets
import status_report
from core import config as core_config
from core import history, paths

REPO_ROOT = paths.find_project_root(__file__)
HISTORY_PATH = history.history_log_path(REPO_ROOT)
CONFIG_PATH = core_config.config_path(REPO_ROOT)

st.set_page_config(page_title="stopslop", page_icon="🛑", layout="wide")


# --- shared helpers ---------------------------------------------------

def _fmt_ts(ts):
    return time.strftime("%H:%M:%S", time.localtime(ts)) if ts else "?"


# Lives in configure.py now (the checks table's "last fired" column needs
# it too, and the import only runs this direction).
_relative_time = _configure.relative_time


def _short_path(file_path):
    if not file_path:
        return ""
    try:
        return os.path.relpath(file_path, REPO_ROOT)
    except ValueError:
        return file_path


# One glyph per gate action, for Watch's activity table. Dropped by accident
# during the vocabulary refactor while its only USE stayed put, so the Watch
# page raised NameError on every render -- see test_dashboard.py, which now
# fails on any name this module reads and never defines.
ACTION_ICON = {"deny": "🚫", "auto_fix": "🔧", "clean": "✅",
               "unscoped_write": "❔", "register_term": "➕", "unregister_term": "➖",
               "config_write": "⚙️"}


def _first_run_notice():
    """Say the one thing a new install needs to hear.

    Nothing on either page told a first-time reader what to do. The footer
    showed `hook: 🔴` and left it there -- a red light with no instruction
    is worse than no light, because it reads as a fault rather than a step
    not taken yet. Shown only while the gate is genuinely not wired up, so
    it disappears the moment it stops being true."""
    report = status_report.build_status_report(REPO_ROOT)
    if report["hook_configured"]:
        return
    st.warning(
        "**The gate is not installed yet.** Everything here reads and edits "
        "config, but no write is being checked. Run `python3 stopslop.py "
        "init` in this repo, then restart Claude Code to pick up the hook. "
        "Until then, use `Try it` on Configure to see what the gate would do.")


def _status_footer():
    # Deliberately no per-event detail here (ruleset/action/file) -- that's
    # already what Watch's own Full activity table shows, in full, one
    # scroll above. This is ambient "is everything okay" status, not a
    # duplicate of content the current page may already be showing -- and
    # it lives in the footer, not the header, so it never competes with
    # the header's real job (brand + navigation) for attention.
    report = status_report.build_status_report(REPO_ROOT)
    config_text = "config: custom" if report["config_file_present"] else "config: default"
    hook_text = "hook: 🟢" if report["hook_configured"] else "hook: 🔴"
    integrity_text = "integrity: 🟢" if report["integrity_baseline_recorded"] else "integrity: ⚪"
    st.caption(
        f"v{report['version']}  ·  {report['gate_event_count']} events  ·  "
        f"{config_text}  ·  {hook_text}  ·  {integrity_text}",
        help="config: whether stopslop.config.json overrides the built-in "
             "defaults, or none exists. hook: is the gate wired into Claude "
             "Code (🔴 = run `stopslop.py init`). integrity: whether a "
             "baseline snapshot of the built-in rule files has ever been "
             "recorded (⚪ = not yet) -- this checks that a snapshot exists, "
             "not that it currently matches.")


# --- Watch --------------------------------------------------------------

def watch_page():
    """Configure answers "what happens to this file?". Watch answers the
    same question in the past tense, so it filters the same way.

    It carried only a ruleset dropdown -- the exact control deleted from
    Configure -- and could not answer "what happened to MY file", which is
    the question anyone opens this page with."""
    _first_run_notice()
    cols = st.columns([3, 2])
    cols[0].text_input("Filter by path", key="watch_path",
                        placeholder="any part of a path, e.g. docs/ or README")
    ids = ["All"] + [m.RULESET_ID for m in rulesets.list_rulesets()]
    cols[1].selectbox("Filter by ruleset", ids, key="watch_filter")
    _watch_activity()


@st.fragment(run_every="2s")
def _watch_activity():
    events = list(reversed(history.read_history_deduped(HISTORY_PATH)))
    chosen = st.session_state.get("watch_filter", "All")
    if chosen != "All":
        events = [e for e in events if e.get("ruleset") == chosen]
    needle = (st.session_state.get("watch_path") or "").strip().lower()
    if needle:
        events = [e for e in events if needle in (e.get("file") or "").lower()]

    denials = [e for e in events if e.get("action") == "deny"][:5]
    with st.container(border=True):
        st.subheader(f"🚫 Recent denials ({len(denials)})" if denials else "🚫 Recent denials")
        if not denials:
            st.caption("None recently -- every write has passed or been auto-fixed.")
        for e in denials:
            st.markdown(f"**{_short_path(e.get('file')) or '(no file)'}** "
                        f"· {e.get('ruleset', '')} · {_relative_time(e.get('ts'))}")
            st.caption("flagged: " + (", ".join(e.get("kinds") or []) or "(no kind recorded)"))

    st.subheader("Full activity")
    events = events[:50]
    if not events:
        st.info("No matching activity yet -- write something through the hook, "
                 "or use `Try it` on Configure to see what it would do.")
        return
    st.dataframe(
        [{
            "time": _fmt_ts(e.get("ts")),
            "event": f"{ACTION_ICON.get(e.get('action'), '')} {e.get('action', '')}".strip(),
            "ruleset": e.get("ruleset", ""),
            "file": _short_path(e.get("file")),
            "kinds": ", ".join(e.get("kinds") or []),
        } for e in events],
        width="stretch", hide_index=True,
    )


# --- Configure -----------------------------------------------------------

# The whole page lives in configure.py: it is the bulk of this dashboard,
# and keeping it here left one module carrying two unrelated jobs (a live
# activity feed and a config editor) with only a comment between them.


def configure_page():
    _first_run_notice()
    _configure.configure_page(REPO_ROOT)


# --- entry point: one header row (brand + nav + pulse), no sidebar ---

watch = st.Page(watch_page, title="Watch", icon="👁", default=True)
configure = st.Page(configure_page, title="Configure", icon="⚙️")
nav = st.navigation([watch, configure], position="hidden")

with st.container(border=True, horizontal=True, vertical_alignment="center"):
    st.markdown("#### 🛑 stopslop")
    st.page_link(watch)
    st.page_link(configure)

nav.run()  # runs the selected page's body inline, right here

st.divider()
_status_footer()
