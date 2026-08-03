#!/usr/bin/env python3
"""Local live dashboard for stopslop, run with `stopslop.py dashboard`.

Two destinations, not five -- Watch and Configure, chosen because that's
the actual split in how a human uses this, not how stopslop's own files
happen to be laid out on disk:

- Watch is passive: what did the gate just do, and why. Denials pulled
  out into their own callout, since a deny is the one event a human
  actually wants explained -- everything else is routine.
- Configure is deliberate: routing (which files a ruleset even sees),
  then one ruleset's checks/thresholds/glossary together in one place,
  plus a "try it" playground scoped to whichever ruleset you're already
  looking at. Previously these lived on three separate tabs, organized
  around which config-file key backed them rather than around "I want to
  tune slopwatch."

A live-status pulse sits in the sidebar, outside both pages, so it stays
visible regardless of which one you're on -- the whole point of a *live*
dashboard is that liveness shouldn't be trapped inside one tab you have
to be looking at.

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
import fnmatch
import os
import sys
import time

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rulesets
import status_report
from core import config as core_config
from core import glossary_packs, history, paths, terms as core_terms

REPO_ROOT = paths.find_project_root(__file__)
HISTORY_PATH = history.history_log_path(REPO_ROOT)
CONFIG_PATH = core_config.config_path(REPO_ROOT)

st.set_page_config(page_title="stopslop", page_icon="🛑", layout="wide")


# --- shared helpers ---------------------------------------------------

def _fmt_ts(ts):
    return time.strftime("%H:%M:%S", time.localtime(ts)) if ts else "?"


def _relative_time(ts):
    if not ts:
        return "?"
    delta = time.time() - ts
    if delta < 60:
        return f"{int(delta)}s ago"
    if delta < 3600:
        return f"{int(delta // 60)}m ago"
    if delta < 86400:
        return f"{int(delta // 3600)}h ago"
    return f"{int(delta // 86400)}d ago"


def _short_path(file_path):
    if not file_path:
        return ""
    try:
        return os.path.relpath(file_path, REPO_ROOT)
    except ValueError:
        return file_path


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
    st.caption(f"v{report['version']}  ·  {report['gate_event_count']} events  ·  "
               f"{config_text}  ·  {hook_text}  ·  {integrity_text}")


# --- Watch --------------------------------------------------------------

def watch_page():
    ids = ["All"] + [m.RULESET_ID for m in rulesets.list_rulesets()]
    st.selectbox("Filter by ruleset", ids, key="watch_filter")
    _watch_activity()


@st.fragment(run_every="2s")
def _watch_activity():
    events = list(reversed(history.read_history_deduped(HISTORY_PATH)))
    chosen = st.session_state.get("watch_filter", "All")
    if chosen != "All":
        events = [e for e in events if e.get("ruleset") == chosen]

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
                 "or try a ruleset's playground on Configure.")
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


# --- Configure ------------------------------------------------------------

def configure_page():
    """Everything a project configures, in one page of flat, project-wide
    tables. There is no separate Vocabulary page and no ruleset radio.

    Both were duplication. The radio picked a ruleset for the checks and
    thresholds blocks while the terms table carried its own ruleset filter
    -- two selectors for one idea. And a Sources block edited pack
    bindings while the Routing editor edited the very same `rulesets[]`
    array, so one config lived behind two controls. Checks, thresholds and
    terms are now each ONE table covering every ruleset, tagged and
    filterable, the same shape as each other."""
    rulesets_with_terms = [m for m in rulesets.list_rulesets() if "terms" in m.CAPABILITIES]

    with st.container(border=True):
        st.subheader("Routing")
        _routing_editor()

    with st.container(border=True):
        st.subheader("Checks")
        _checks_table()

    with st.container(border=True):
        st.subheader("Thresholds")
        _thresholds_table()

    with st.container(border=True):
        st.subheader("Terms")
        _terms_table()
        _add_term_form(rulesets_with_terms)
        _suppressed_section()

    with st.container(border=True):
        _playground_section()


def _routing_editor():
    """Which ruleset gates which path. Nothing else.

    This used to also carry a read-only `packs` column and an "attach
    vocabulary packs" expander -- data in one place and the control in
    another, and both about vocabulary rather than routing. Packs are a
    SOURCE OF TERMS, so they live in Terms, next to the words they add."""
    st.caption(f"`{os.path.relpath(CONFIG_PATH, REPO_ROOT)}` -- first match wins. "
               "Changes apply to the next gate call immediately, no restart.")
    ids = [m.RULESET_ID for m in rulesets.list_rulesets()]
    edited = st.data_editor(
        [{"glob": g, "ruleset": r or ""} for g, r, _ in core_config.rule_packs(REPO_ROOT)],
        num_rows="dynamic", width="stretch", key="config_editor",
        column_config={
            "glob": st.column_config.TextColumn("glob", required=True),
            "ruleset": st.column_config.SelectboxColumn(
                "ruleset", options=[""] + ids,
                help="Empty means out of scope entirely (like .claude/*)."),
        })
    if st.button("Save routing"):
        try:
            core_config.save_rules(
                REPO_ROOT,
                [{"glob": r["glob"], "ruleset": r["ruleset"] or None}
                 for r in edited if r.get("glob")],
                rulesets)
            st.toast("Routing saved", icon="✅")
            st.rerun()
        except Exception as exc:
            st.error(f"Not saved: {exc}")


def _filter_row(rows, text_fields, facets, key):
    """Search box plus one multiselect per facet, returning the filtered
    rows. Shared so the Checks and Terms tables cannot drift into two
    different standards for the same interaction, which is exactly what
    happened when only one of them had filters."""
    cols = st.columns([3] + [2] * len(facets))
    needle = cols[0].text_input("Search", key=f"{key}_q").strip().lower()
    picked = {}
    for i, facet in enumerate(facets):
        chosen = cols[i + 1].multiselect(
            facet.replace("_", " ").title(), sorted({r[facet] for r in rows}),
            key=f"{key}_{facet}")
        if chosen:
            picked[facet] = set(chosen)

    out = [r for r in rows
           if (not needle or any(needle in str(r[f]).lower() for f in text_fields))
           and all(r[f] in vals for f, vals in picked.items())]
    if len(out) != len(rows):
        st.caption(f"{len(out)} of {len(rows)} shown")
    return out


def _checks_table():
    """Every check every ruleset ships, in one table -- the same shape the
    terms table uses, rather than a wall of checkboxes behind a ruleset
    radio."""
    rows = []
    for module in rulesets.list_rulesets():
        if "checks" not in module.CAPABILITIES:
            continue
        for cid, meta in sorted(module.list_checks().items()):
            rows.append({"enabled": meta["enabled"], "check": cid,
                          "ruleset": module.RULESET_ID,
                          "what it catches": meta["description"] or ""})
    if not rows:
        st.caption("No ruleset exposes individually-toggleable checks.")
        return

    off = sum(1 for r in rows if not r["enabled"])
    st.caption(f"{len(rows)} checks · {off} off" if off else f"{len(rows)} checks, all on")
    shown = _filter_row(rows, ("check", "what it catches"), ("ruleset",), "chk")
    if not shown:
        st.caption("Nothing matches.")
        return
    edited = st.data_editor(
        shown, width="stretch", hide_index=True, key="checks_table",
        column_config={
            "enabled": st.column_config.CheckboxColumn("on", width="small"),
            "check": st.column_config.TextColumn("check", disabled=True),
            "ruleset": st.column_config.TextColumn("ruleset", disabled=True, width="small"),
            "what it catches": st.column_config.TextColumn(
                "what it catches", disabled=True, width="large"),
        })
    if st.button("Save checks"):
        by_ruleset = {}
        for row in edited:
            by_ruleset.setdefault(row["ruleset"], []).append(row)
        try:
            for ruleset_id, group in by_ruleset.items():
                rulesets.get_ruleset(ruleset_id).set_enabled_checks(
                    [r["check"] for r in group if r["enabled"]])
            st.toast("Checks saved", icon="✅")
            st.rerun()
        except Exception as exc:
            st.error(f"Not saved: {exc}")


def _thresholds_table():
    rows = []
    for module in rulesets.list_rulesets():
        if "options" not in module.CAPABILITIES:
            continue
        for name, info in sorted(module.list_options().items()):
            rows.append({"option": name, "ruleset": module.RULESET_ID,
                          "value": info["value"], "default": info["default"]})
    if not rows:
        st.caption("No ruleset exposes tunable thresholds.")
        return
    edited = st.data_editor(
        rows, width="stretch", hide_index=True, key="options_table",
        column_config={
            "option": st.column_config.TextColumn("option", disabled=True),
            "ruleset": st.column_config.TextColumn("ruleset", disabled=True, width="small"),
            "value": st.column_config.NumberColumn("value", step=1),
            "default": st.column_config.NumberColumn("default", disabled=True),
        })
    if st.button("Save thresholds"):
        by_ruleset = {}
        for row in edited:
            by_ruleset.setdefault(row["ruleset"], {})[row["option"]] = int(row["value"])
        try:
            for ruleset_id, values in by_ruleset.items():
                rulesets.get_ruleset(ruleset_id).set_options(values)
            st.toast("Thresholds saved", icon="✅")
            st.rerun()
        except Exception as exc:
            st.error(f"Not saved: {exc}")


def _terms_table():
    """Every term, for one resolved path, with the sources that supply them.

    The path input is not a convenience. Packs attach to the routing rule
    that matches a file, so two files handled by the same ruleset genuinely
    have different vocabularies -- and this table used to resolve silently
    against the synthetic free-text path, showing what a `.md` file happens
    to get while presenting it as the project's vocabulary."""
    head = st.columns([2, 5])
    default = core_config.SYNTHETIC_TEXT_NAME
    probe = head[0].text_input("Resolve for path", value=default,
                                key="terms_path").strip() or default
    full = os.path.join(REPO_ROOT, probe)
    matched = core_config.resolve_ruleset_id(full, REPO_ROOT)
    rows = core_terms.term_index(rulesets, REPO_ROOT, file_path=full)
    with head[1]:
        st.caption("")
        st.caption(f"`{probe}` is gated by **{matched or 'nothing (out of scope)'}** · "
                   f"**{len(rows)}** terms from **{len({r['source'] for r in rows})}** "
                   f"sources. Every ruleset is listed; filter to narrow.")

    _sources_table(rows, probe, full)

    shown = _filter_row(rows, ("term", "note"),
                         ("ruleset", "list", "source", "polarity"), "trm")
    if not shown:
        st.caption("Nothing matches.")
        return

    event = st.dataframe(
        shown, width="stretch", hide_index=True, height=380,
        on_select="rerun", selection_mode="multi-row", key="terms_table",
        column_config={
            "term": st.column_config.TextColumn("term", width="medium"),
            "ruleset": st.column_config.TextColumn("ruleset", width="small"),
            "list": st.column_config.TextColumn("list", width="small"),
            "source": st.column_config.TextColumn("source", width="small"),
            "polarity": st.column_config.TextColumn("polarity", width="small"),
            "note": st.column_config.TextColumn("note", width="large"),
        })

    picked = [shown[i] for i in event.selection.rows]
    if not picked:
        st.caption("Select rows to remove them. A shipped term -- a built-in or "
                   "a pack word -- is suppressed rather than deleted, since the "
                   "word lives in a ruleset's source or a shipped pack, and can "
                   "be restored below.")
        return
    if st.button(f"Remove {len(picked)} selected", type="primary", key="rm_sel"):
        results = []
        for row in picked:
            module = rulesets.get_ruleset(row["ruleset"])
            try:
                results.append(module.remove_term(row["list"], row["term"]))
            except Exception as exc:
                results.append({"ok": False, "message": str(exc)})
        failed = [r for r in results if not r.get("ok")]
        for r in failed:
            st.error(r.get("message", ""))
        if not failed:
            st.toast(f"{len(results)} term(s) removed.", icon="✅")
        st.rerun()


def _sources_table(rows, probe, full_path):
    """Where this path's terms come from, and the one control that changes
    it. Counted from the same rows the table below renders, so the summary
    can never disagree with the detail."""
    counts = {}
    for row in rows:
        counts[(row["source"], row["ruleset"], row["list"])] = \
            counts.get((row["source"], row["ruleset"], row["list"]), 0) + 1
    packs = set(glossary_packs.AVAILABLE_PACKS)
    kind = lambda src: "pack" if src in packs else ("yours" if src == "yours" else "shipped")

    with st.expander(f"Sources — {len(counts)} feeding `{probe}`"):
        st.dataframe(
            [{"kind": kind(src), "source": src, "feeds": f"{rs}.{lid}", "terms": n}
             for (src, rs, lid), n in sorted(counts.items(),
                                              key=lambda kv: (-kv[1], kv[0]))],
            width="stretch", hide_index=True)

        attached = [(src, rs, lid) for (src, rs, lid) in counts if src in packs]
        cols = st.columns([2, 2, 1])
        pack = cols[0].selectbox("Pack", sorted(packs), key="attach_pack",
                                  format_func=lambda p: f"{p} "
                                      f"({glossary_packs.pack_meta(p)['term_count']})")
        targets = [(m.RULESET_ID, lid) for m in rulesets.list_rulesets()
                    if "terms" in m.CAPABILITIES
                    for lid, spec in sorted(m.TERM_LISTS.items())
                    if spec.get("accepts_packs")]
        target = cols[1].selectbox("Feeds", targets, key="attach_list",
                                    format_func=lambda t: f"{t[0]}.{t[1]}")
        on = (pack, target[0], target[1]) in attached
        with cols[2]:
            st.caption("")
            label = "Detach" if on else "Attach"
            if st.button(label, key="attach_btn"):
                _set_pack(full_path, pack, target, attach=not on)

        polarity = rulesets.get_ruleset(target[0]).TERM_LISTS[target[1]]["polarity"]
        if polarity == "deny" and not on:
            st.caption("⚠️ That is a deny list — every word in the pack would "
                       "become something the gate flags.")


def _set_pack(full_path, pack, target, attach):
    """Attach or detach one pack on the rule that matches the current path,
    so the control acts on exactly the resolution shown above it."""
    ruleset_id, list_id = target
    for glob, rs, by_list in core_config.rule_packs(REPO_ROOT):
        if rs != ruleset_id or not fnmatch.fnmatch(
                os.path.relpath(full_path, REPO_ROOT).replace(os.sep, "/"), glob):
            continue
        current = list(by_list.get(list_id, []))
        new = current + [pack] if attach else [p for p in current if p != pack]
        try:
            core_config.set_rule_packs(REPO_ROOT, glob, list_id, new,
                                        known_packs=glossary_packs.AVAILABLE_PACKS)
            st.toast(f"{glob} → {list_id}: {', '.join(new) or '(none)'}", icon="✅")
            st.rerun()
        except Exception as exc:
            st.error(f"Not saved: {exc}")
        return
    st.warning(f"No routing rule sends this path to {ruleset_id}, so there is "
               f"nothing to attach the pack to. Add a rule in Routing first.")


def _add_term_form(term_rulesets):
    targets = [(m.RULESET_ID, lid) for m in term_rulesets
                for lid in sorted(m.TERM_LISTS)]
    with st.form("addterm", clear_on_submit=True):
        cols = st.columns([2, 2, 3, 2, 1])
        target = cols[0].selectbox("List", targets,
                                    format_func=lambda t: f"{t[0]}.{t[1]}")
        term = cols[1].text_input("Term")
        note = cols[2].text_input("Note")
        force = cols[3].text_input(
            "Override reason",
            help="Only needed when the ruleset's own standard already forbids "
                  "the word. Goes on the record.")
        if cols[4].form_submit_button("Add") and term:
            module = rulesets.get_ruleset(target[0])
            try:
                result = module.add_term(target[1], term, note, force=force or False)
            except Exception as exc:
                st.error(f"Not saved: {exc}")
                return
            st.toast(result.get("message", ""), icon="✅" if result.get("ok") else "🚫")
            st.rerun()


def _suppressed_section():
    rows = core_terms.suppressed_index(rulesets, REPO_ROOT)
    if not rows:
        return
    with st.expander(f"{len(rows)} suppressed term(s)"):
        st.caption("Removed from a built-in or a pack. The word still exists in "
                   "its source; this project just does not use it here.")
        event = st.dataframe(rows, width="stretch", hide_index=True,
                              on_select="rerun", selection_mode="multi-row",
                              key="suppressed_table")
        picked = [rows[i] for i in event.selection.rows]
        if picked and st.button(f"Restore {len(picked)}", key="restore_sel"):
            for row in picked:
                rulesets.get_ruleset(row["ruleset"]).add_term(row["list"], row["term"])
            st.toast(f"{len(picked)} term(s) restored.", icon="✅")
            st.rerun()


def _playground_section():
    """Free text against a chosen ruleset. This is the one place a ruleset
    picker genuinely belongs -- it names what to run, rather than scoping a
    page that is otherwise project-wide."""
    st.subheader("Try it")
    ids = [m.RULESET_ID for m in rulesets.list_rulesets()]
    cols = st.columns([1, 4])
    ruleset_id = cols[0].selectbox("Ruleset", ids, key="playground_ruleset")
    text = cols[1].text_area("Text", height=120, key="playground_text",
                              placeholder="Paste a sentence or a snippet...")
    if not (st.button("Lint it", type="primary", key="lint_btn") and text.strip()):
        return

    ruleset = rulesets.get_ruleset(ruleset_id)
    result = ruleset.lint_and_gate(text)
    blocking = ruleset.blocking_semantic_flags(result["semantic_flags"])
    if blocking:
        st.error(f"Would DENY -- {len(blocking)} flag(s) need a person's judgment")
        for f in blocking:
            st.write(f"- **[{f['kind']}]** {f.get('label') or ''} -- "
                     f"{f['detail'].get('note', '')}")
    elif result["mechanical_violations"]:
        st.warning(f"Would AUTO-FIX -- {len(result['mechanical_violations'])} "
                   f"mechanical violation(s)")
        st.code(ruleset.apply_mechanical_fixes(text))
    else:
        st.success("Would PASS unchanged")
    non_blocking = [f for f in result["semantic_flags"] if f not in blocking]
    if non_blocking:
        with st.expander(f"{len(non_blocking)} non-blocking note(s)"):
            for f in non_blocking:
                st.write(f"- [{f['kind']}] {f.get('label') or ''}")


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
