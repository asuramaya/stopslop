#!/usr/bin/env python3
"""Local live dashboard for stopslop, run with `stopslop.py dashboard`.

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
import rulesets
import status_report
from core import config as core_config
from core import history, paths

REPO_ROOT = paths.find_project_root(__file__)
HISTORY_PATH = history.history_log_path(REPO_ROOT)
CONFIG_PATH = core_config.config_path(REPO_ROOT)

st.set_page_config(page_title="stopslop", page_icon="🛑", layout="wide")


def _fmt_ts(ts):
    return time.strftime("%H:%M:%S", time.localtime(ts)) if ts else "?"


def _short_path(file_path):
    if not file_path:
        return ""
    try:
        return os.path.relpath(file_path, REPO_ROOT)
    except ValueError:
        return file_path


ACTION_ICON = {"deny": "🚫", "auto_fix": "🔧", "clean": "✅",
               "unscoped_write": "❔", "register_term": "➕", "unregister_term": "➖"}


@st.fragment(run_every="2s")
def activity_and_status():
    report = status_report.build_status_report(REPO_ROOT)

    # Two rows of at most 3 metrics rather than one row of 5 -- stays
    # readable at any viewport width instead of squeezing on a narrow one.
    row1 = st.columns(3)
    row1[0].metric("version", report["version"])
    row1[1].metric("gate events", report["gate_event_count"])
    row1[2].metric("hook wiring", "on" if report["hook_configured"] else "OFF")
    row2 = st.columns(3)
    row2[0].metric("integrity", "ok" if report["integrity_baseline_recorded"] else "none yet")
    row2[1].metric("config file", "custom" if report["config_file_present"] else "default")

    # Stacked, not side-by-side columns -- a ruleset's stat list is
    # variable-length (codewatch has none beyond "checks", ste100 has
    # three), so a fixed-width column either wastes space or clips.
    for rs in report["rulesets"]:
        stat_line = " · ".join(f"{k.replace('_', ' ')}: {v}" for k, v in rs["stats"].items()
                                if k != "checks")  # the check-name list is long, not a one-liner
        st.caption(f"**{rs['name']}** ({rs['id']})" + (f" — {stat_line}" if stat_line else ""))

    st.subheader("Live activity")
    events = list(reversed(history.read_history_deduped(HISTORY_PATH)))[:50]
    if not events:
        st.info("No gate activity yet -- write something through the hook, or lint text below.")
        return
    st.dataframe(
        [{
            "time": _fmt_ts(e.get("ts")),
            "": ACTION_ICON.get(e.get("action"), ""),
            "ruleset": e.get("ruleset", ""),
            "action": e.get("action", ""),
            "file": _short_path(e.get("file")),
            "kinds": ", ".join(e.get("kinds") or []),
        } for e in events],
        use_container_width=True, hide_index=True,
    )


def lint_playground():
    st.subheader("Lint playground")
    st.caption("Check text the same way the live gate would, without writing it anywhere.")
    ids = [m.RULESET_ID for m in rulesets.list_rulesets()]
    ruleset_id = st.selectbox("Ruleset", ids, key="playground_ruleset")
    text = st.text_area("Text", height=120, key="playground_text",
                         placeholder="Paste a sentence or a snippet...")
    if st.button("Lint it", type="primary") and text.strip():
        active = rulesets.get_ruleset(ruleset_id)
        result = active.lint_and_gate(text)
        blocking = active.blocking_semantic_flags(result["semantic_flags"])
        if blocking:
            st.error(f"Would DENY -- {len(blocking)} flag(s) need a person's judgment")
            for f in blocking:
                st.write(f"- **[{f['kind']}]** {f.get('label') or ''} -- "
                         f"{f['detail'].get('note', '')}")
        elif result["mechanical_violations"]:
            st.warning(f"Would AUTO-FIX -- {len(result['mechanical_violations'])} "
                       f"mechanical violation(s)")
            st.code(active.apply_mechanical_fixes(text))
        else:
            st.success("Would PASS unchanged")
        non_blocking = [f for f in result["semantic_flags"] if f not in blocking]
        if non_blocking:
            with st.expander(f"{len(non_blocking)} non-blocking note(s)"):
                for f in non_blocking:
                    st.write(f"- [{f['kind']}] {f.get('label') or ''}")


def config_editor():
    st.subheader("Routing configuration")
    st.caption(f"`{CONFIG_PATH}` -- picks which ruleset lints which file, first match wins. "
               "Changes apply to the next gate call immediately, no session restart needed.")
    rules = core_config.load_rules(REPO_ROOT)
    ids = [m.RULESET_ID for m in rulesets.list_rulesets()]
    rows = [{"glob": r["glob"], "ruleset": r["ruleset"] or ""} for r in rules]

    edited = st.data_editor(
        rows, num_rows="dynamic", use_container_width=True, key="config_editor",
        column_config={
            "glob": st.column_config.TextColumn("glob", required=True),
            "ruleset": st.column_config.SelectboxColumn(
                "ruleset", options=[""] + ids,
                help="Empty means out of scope entirely (like .claude/*)."),
        },
    )
    if st.button("Save routing config"):
        new_rules = [{"glob": r["glob"], "ruleset": r["ruleset"] or None}
                     for r in edited if r.get("glob")]
        try:
            core_config.save_rules(REPO_ROOT, new_rules, rulesets)
            st.success(f"Wrote {len(new_rules)} rule(s) to stopslop.config.json")
        except Exception as exc:
            st.error(f"Not saved: {exc}")


def glossary_editor():
    glossary_rulesets = [m for m in rulesets.list_rulesets() if "glossary" in m.CAPABILITIES]
    if not glossary_rulesets:
        st.info("No registered ruleset declares a glossary capability.")
        return
    for ruleset in glossary_rulesets:
        st.subheader(f"{ruleset.RULESET_NAME} glossary")
        terms = ruleset.list_terms()
        st.caption(f"{len(terms)} registered term(s)")
        if terms:
            st.dataframe(
                [{"word": w, "note": t.get("note", ""),
                  "overrides a real rule": bool(t.get("overrides_unapproved"))}
                 for w, t in sorted(terms.items())],
                use_container_width=True, hide_index=True,
            )

        with st.form(key=f"register_{ruleset.RULESET_ID}", clear_on_submit=True):
            cols = st.columns([2, 3, 2, 1])
            word = cols[0].text_input("word")
            note = cols[1].text_input("note")
            override = cols[2].text_input("override reason (only if the word is already forbidden)")
            submitted = cols[3].form_submit_button("Register")
            if submitted and word:
                result = ruleset.register_term(word, note, override or None)
                # toast + rerun, not st.success -- a plain success message
                # would render into a script run that's about to be thrown
                # away by rerun(), and without the rerun the table above
                # keeps showing the pre-registration term count/list until
                # some unrelated later interaction happens to refresh it.
                st.toast(result["message"], icon="✅" if result["ok"] else "🚫")
                st.rerun()

        unreg_col, btn_col = st.columns([4, 1])
        word_to_remove = unreg_col.text_input("word to unregister", key=f"unreg_{ruleset.RULESET_ID}")
        if btn_col.button("Unregister", key=f"unreg_btn_{ruleset.RULESET_ID}") and word_to_remove:
            result = ruleset.unregister_term(word_to_remove)
            st.toast(result["message"], icon="✅" if result["ok"] else "🚫")
            st.rerun()

        if "word_lookup" in ruleset.CAPABILITIES:
            check = st.text_input(f"check a single word against {ruleset.RULESET_ID}",
                                   key=f"check_{ruleset.RULESET_ID}")
            if check:
                st.json(ruleset.check_word(check))


st.title("🛑 stopslop")
tab_activity, tab_playground, tab_config, tab_glossary = st.tabs(
    ["Activity", "Lint playground", "Configuration", "Glossary"])

with tab_activity:
    activity_and_status()
with tab_playground:
    lint_playground()
with tab_config:
    config_editor()
with tab_glossary:
    glossary_editor()
