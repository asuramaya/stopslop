#!/usr/bin/env python3
"""Local live dashboard for stopslop, run with `stopslop.py dashboard`.

Two destinations, not five -- Watch and Configure, chosen because that's
the actual split in how a human uses this, not how stopslop's own files
happen to be laid out on disk:

- Watch is passive: what did the gate just do, and why. Denials pulled
  out into their own callout, since a deny is the one event a human
  actually wants explained -- everything else is routine.
- Configure is deliberate, and answers ONE question: what happens to this
  file? A path at the top, then routing, checks, thresholds, vocabulary
  and a playground, each answering its own part of that question for that
  path. Sections do not re-ask it -- there is one path box on the page
  and no ruleset dropdown anywhere, because a path already implies its
  ruleset and two controls for one idea can disagree.

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
    """Everything a project configures, in one page of flat tables, under
    ONE context control: a path.

    The page answers a single question -- what happens to this file? --
    and every section answers its own part of it: which ruleset gates it,
    which checks run, at what thresholds, with what vocabulary, and (Try
    it) what that combination actually decides. Sections do not each
    re-ask the question. There was a path box inside Terms and a separate
    ruleset dropdown inside Try it, so the page had two answers to "what
    am I looking at" and they could disagree: you could read the
    vocabulary for `docs/guide.md` and then lint against a ruleset that
    file never routes to. Try it also never passed the path down, so it
    silently resolved packs for the synthetic free-text path -- 187 terms
    adrift from what the real gate would use, and no way to tell from the
    screen.

    Checks and thresholds stay project-wide, because they genuinely are:
    they are per-ruleset settings, not per-path ones. The path narrows
    what is worth looking at, it does not hide the rest."""
    probe, full, ruleset_id = _page_scope()

    with st.container(border=True):
        st.subheader("Routing")
        _routing_editor()

    with st.container(border=True):
        st.subheader("Checks")
        _checks_table(ruleset_id)

    with st.container(border=True):
        st.subheader("Thresholds")
        _thresholds_table(ruleset_id)

    with st.container(border=True):
        st.subheader("Terms")
        _terms_table(probe, full, ruleset_id)
        _add_term_form()
        _suppressed_section()

    with st.container(border=True):
        _playground_section(probe, full, ruleset_id)


def _page_scope():
    """The page's one context control. Returns (probe, full path, ruleset id).

    Stated once, in one sentence, naming the rule that matched -- so the
    Routing table below reads as the explanation of this line rather than
    as an unrelated grid the reader has to resolve in their head."""
    cols = st.columns([2, 5])
    default = core_config.SYNTHETIC_TEXT_NAME
    probe = cols[0].text_input(
        "Configuring for path", value=default, key="scope_path",
        help="Any path in this repo. Routing decides the rest; the default "
             "is the synthetic name free text is treated as.").strip() or default
    full = os.path.join(REPO_ROOT, probe)
    rule = core_config.matching_rule(full, REPO_ROOT)
    ruleset_id = rule["ruleset"] if rule else None
    with cols[1]:
        st.caption("")
        if ruleset_id:
            st.markdown(f"`{probe}` → gated by **{ruleset_id}**, "
                        f"by the rule `{rule['glob']}`")
        elif rule:
            st.markdown(f"`{probe}` → **not gated**: the rule `{rule['glob']}` "
                        f"puts it out of scope on purpose")
        else:
            st.markdown(f"`{probe}` → **not gated**: no routing rule matches it")
    return probe, full, ruleset_id


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
        incoming = [{"glob": r["glob"], "ruleset": r["ruleset"] or None}
                    for r in edited if r.get("glob")]
        # save_rules carries packs forward by GLOB, so editing a glob in
        # place ("*.md" -> "docs/*.md") reads as deleting one rule and
        # adding another, and that rule's packs go with it. That is the
        # right merge rule -- a glob is the rule's identity -- but it must
        # not happen quietly, so say which packs a save is about to drop.
        kept = {r["glob"] for r in incoming}
        orphaned = {g: sum(len(v) for v in packs.values())
                    for g, _, packs in core_config.rule_packs(REPO_ROOT)
                    if packs and g not in kept}
        try:
            core_config.save_rules(REPO_ROOT, incoming, rulesets)
            for glob, count in orphaned.items():
                st.warning(f"Rule `{glob}` is gone, and the {count} pack "
                           f"binding(s) on it went with it. Re-attach them "
                           f"under Terms if the new rule needs them.")
            if not orphaned:
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


def _checks_table(scope_ruleset=None):
    """Every check every ruleset ships, in one table.

    Two columns, not one sentence: a check is "what it catches" and "what
    to do instead", and gluing them into prose is what produced 37 of 43
    rows opening with the same words. See a ruleset's own CHECKS."""
    rows = []
    for module in rulesets.list_rulesets():
        if "checks" not in module.CAPABILITIES:
            continue
        for cid, meta in sorted(module.list_checks().items()):
            rows.append({"enabled": meta["enabled"], "check": cid,
                          "ruleset": module.RULESET_ID,
                          "catches": meta["catches"], "instead": meta["instead"]})
    if not rows:
        st.caption("No ruleset exposes individually-toggleable checks.")
        return

    off = sum(1 for r in rows if not r["enabled"])
    here = sum(1 for r in rows if r["ruleset"] == scope_ruleset and r["enabled"])
    st.caption(f"{len(rows)} checks across every ruleset, {off} off. "
               + (f"**{here}** of them run on this path."
                  if scope_ruleset else "None run on this path."))
    shown = _filter_row(rows, ("check", "catches", "instead"), ("ruleset",), "chk")
    if not shown:
        st.caption("Nothing matches.")
        return
    edited = st.data_editor(
        shown, width="stretch", hide_index=True, key="checks_table",
        column_config={
            "enabled": st.column_config.CheckboxColumn("on", width="small"),
            "check": st.column_config.TextColumn("check", disabled=True),
            "ruleset": st.column_config.TextColumn("ruleset", disabled=True, width="small"),
            "catches": st.column_config.TextColumn(
                "what it catches", disabled=True, width="large"),
            "instead": st.column_config.TextColumn(
                "do this instead", disabled=True, width="large"),
        })
    if st.button("Save checks"):
        # set_checks_enabled MERGES, which is the only correct shape here:
        # this editor holds whatever rows survived the filter, never the
        # whole set. It used to call set_enabled_checks, which REPLACES --
        # so typing "filler" in the search box and pressing Save read as
        # "enable exactly these two" and turned off 18 of slopwatch's 20
        # checks, with a success toast and nothing on screen to notice.
        by_ruleset = {}
        for row in edited:
            by_ruleset.setdefault(row["ruleset"], {})[row["check"]] = row["enabled"]
        try:
            for ruleset_id, states in by_ruleset.items():
                rulesets.get_ruleset(ruleset_id).set_checks_enabled(states)
            st.toast("Checks saved", icon="✅")
            st.rerun()
        except Exception as exc:
            st.error(f"Not saved: {exc}")


def _thresholds_table(scope_ruleset=None):
    """One qualified name per row, not a bare name plus a ruleset column.

    `block_flag_count_threshold` appeared twice, identical, distinguishable
    only by reading sideways into a second column -- the reader had to join
    two fields to know which row was which. `codewatch.block_flag_count_
    threshold` is the name of the thing."""
    rows, rulesets_of = [], {}
    for module in rulesets.list_rulesets():
        if "options" not in module.CAPABILITIES:
            continue
        for name, info in sorted(module.list_options().items()):
            qualified = f"{module.RULESET_ID}.{name}"
            rulesets_of[qualified] = (module.RULESET_ID, name)
            rows.append({"threshold": qualified, "value": info["value"],
                          "default": info["default"]})
    if not rows:
        st.caption("No ruleset exposes tunable thresholds.")
        return
    changed = [r["threshold"] for r in rows if r["value"] != r["default"]]
    here = [r["threshold"] for r in rows
            if r["threshold"].startswith(f"{scope_ruleset}.")] if scope_ruleset else []
    # Say "none apply here" when none do. ste100 ships no tunable
    # thresholds at all, so a line inviting the reader to look for
    # `ste100.` ones sends them hunting for something that cannot exist.
    scope_note = (f" {len(here)} of them apply to this path." if here else
                   " None of them apply to this path.")
    st.caption((", ".join(changed) + " differ from their shipped defaults."
                if changed else "All at their shipped defaults.") + scope_note)
    edited = st.data_editor(
        rows, width="stretch", hide_index=True, key="options_table",
        column_config={
            "threshold": st.column_config.TextColumn("threshold", disabled=True,
                                                      width="large"),
            "value": st.column_config.NumberColumn("value", step=1, width="small"),
            "default": st.column_config.NumberColumn("shipped default",
                                                      disabled=True, width="small"),
        })
    if st.button("Save thresholds"):
        by_ruleset = {}
        for row in edited:
            ruleset_id, name = rulesets_of[row["threshold"]]
            by_ruleset.setdefault(ruleset_id, {})[name] = int(row["value"])
        try:
            for ruleset_id, values in by_ruleset.items():
                rulesets.get_ruleset(ruleset_id).set_options(values)
            st.toast("Thresholds saved", icon="✅")
            st.rerun()
        except Exception as exc:
            st.error(f"Not saved: {exc}")


def _terms_table(probe, full, scope_ruleset=None):
    """Every term the scoped path resolves to, and the sources supplying them.

    Four columns, because the other two were derivable from these. `ruleset`
    and `list` were separate columns that only ever read as one name, and
    `polarity` is a property of the LIST -- every row of an allow list said
    "allow", 2830 times. Both survive as filter facets, where a derived
    value is useful; neither earns a column of its own."""
    rows = core_terms.term_index(rulesets, REPO_ROOT, file_path=full)
    for row in rows:
        row["list"] = f"{row['ruleset']}.{row['list']}"
    st.caption(f"**{len(rows)}** terms reach `{probe}`. Every ruleset's lists "
               f"are here; filter to narrow.")

    _sources_block(rows, full, scope_ruleset)

    shown = _filter_row(rows, ("term", "note"),
                         ("ruleset", "list", "source", "polarity"), "trm")
    if not shown:
        st.caption("Nothing matches.")
        return

    event = st.dataframe(
        [{k: r[k] for k in ("term", "list", "source", "note")} for r in shown],
        width="stretch", hide_index=True, height=380,
        on_select="rerun", selection_mode="multi-row", key="terms_table",
        column_config={
            "term": st.column_config.TextColumn("term", width="medium"),
            "list": st.column_config.TextColumn("list", width="medium"),
            "source": st.column_config.TextColumn("source", width="medium"),
            "note": st.column_config.TextColumn("note", width="large"),
        })

    picked = [shown[i] for i in event.selection.rows]
    if not picked:
        st.caption("Select rows to remove them. A shipped word -- a built-in or "
                   "one from a pack -- is suppressed rather than deleted, since "
                   "it lives in a ruleset's source or a shipped pack. Suppressed "
                   "words are restorable below.")
        return
    if st.button(f"Remove {len(picked)} selected", type="primary", key="rm_sel"):
        results = []
        for row in picked:
            module = rulesets.get_ruleset(row["ruleset"])
            try:
                results.append(module.remove_term(row["list"].split(".", 1)[1],
                                                   row["term"]))
            except Exception as exc:
                results.append({"ok": False, "message": str(exc)})
        failed = [r for r in results if not r.get("ok")]
        for r in failed:
            st.error(r.get("message", ""))
        if not failed:
            st.toast(f"{len(results)} term(s) removed.", icon="✅")
        st.rerun()


def _sources_block(rows, full_path, scope_ruleset=None):
    """Where this path's terms come from, and the one control that changes
    it -- counted off the same rows the table renders, so the summary can
    never disagree with the detail.

    One row per source, not one per source-and-list. Two adjacent lines used
    to state the source count differently ("from 5 sources" over "Sources --
    12 feeding"), both correct, because one counted names and the other
    counted bindings. A source that feeds two lists is still one source; the
    lists it feeds belong in a column.

    Not an expander any more. The attach control is the only way to change
    what vocabulary a path gets, and it was folded inside a collapsed
    disclosure titled "Sources"."""
    packs = set(glossary_packs.AVAILABLE_PACKS)
    by_source = {}
    for row in rows:
        entry = by_source.setdefault(row["source"], {"terms": 0, "feeds": set()})
        entry["terms"] += 1
        entry["feeds"].add(row["list"])

    st.dataframe(
        [{"source": src,
          "kind": "pack" if src in packs else ("yours" if src == "yours" else "shipped"),
          "terms": e["terms"], "feeds": ", ".join(sorted(e["feeds"]))}
         for src, e in sorted(by_source.items(), key=lambda kv: (-kv[1]["terms"], kv[0]))],
        width="stretch", hide_index=True)

    attached = {(src, lid) for src, e in by_source.items() if src in packs
                for lid in e["feeds"]}
    cols = st.columns([2, 2, 1])
    pack = cols[0].selectbox(
        "Pack", sorted(packs), key="attach_pack",
        format_func=lambda p: f"{p} ({glossary_packs.pack_meta(p)['term_count']} terms)")
    targets = [(m.RULESET_ID, lid) for m in rulesets.list_rulesets()
                if "terms" in m.CAPABILITIES
                for lid, spec in sorted(m.TERM_LISTS.items())
                if spec.get("accepts_packs")]
    # Lists belonging to the ruleset that actually gates this path come
    # first, so the default selection is one that can fire. Left in plain
    # alphabetical order, the default was codewatch.generic_naming -- a
    # deny list -- which meant the "every word in this pack would become
    # something the gate flags" warning greeted everyone on arrival,
    # attached to a choice nobody had made.
    targets.sort(key=lambda t: (t[0] != scope_ruleset, t[0], t[1]))
    target = cols[1].selectbox("Feeds which list", targets, key="attach_list",
                                format_func=lambda t: f"{t[0]}.{t[1]}")
    on = (pack, f"{target[0]}.{target[1]}") in attached
    with cols[2]:
        st.caption("")
        if st.button("Detach" if on else "Attach", key="attach_btn"):
            _set_pack(full_path, pack, target, attach=not on)

    if not on and rulesets.get_ruleset(target[0]).TERM_LISTS[target[1]]["polarity"] == "deny":
        st.caption("⚠️ That is a deny list — every word in the pack would "
                   "become something the gate flags.")


def _set_pack(full_path, pack, target, attach):
    """Attach or detach one pack on the rule that ACTUALLY gates this path.

    Resolved through core_config.matching_rule, the same first-match-wins
    call the gate makes. This used to scan for the first rule matching both
    the path and the chosen ruleset, which is a different question and could
    answer with a rule the gate never reaches -- writing a binding that
    silently could not fire."""
    ruleset_id, list_id = target
    rule = core_config.matching_rule(full_path, REPO_ROOT)
    if rule is None or rule["ruleset"] != ruleset_id:
        gated_by = (rule or {}).get("ruleset") or "nothing"
        st.warning(f"This path is gated by {gated_by}, not {ruleset_id}, so a "
                   f"{ruleset_id} pack attached here could never fire. Point "
                   f"the path box at a file {ruleset_id} actually gates, or "
                   f"change the rule in Routing.")
        return
    current = list((rule.get("packs") or {}).get(list_id, []))
    new = current + [pack] if attach else [p for p in current if p != pack]
    try:
        core_config.set_rule_packs(REPO_ROOT, rule["glob"], list_id, new,
                                    known_packs=glossary_packs.AVAILABLE_PACKS)
        st.toast(f"{rule['glob']} → {list_id}: {', '.join(new) or '(none)'}", icon="✅")
        st.rerun()
    except Exception as exc:
        st.error(f"Not saved: {exc}")


def _add_term_form():
    """Add one word. Three fields, and a fourth only when it means something.

    "Override reason" used to sit here permanently, dead for eight of the
    nine lists: only ste100's project vocabulary has a real external
    standard that can refuse a word in the first place. So the form now
    just tries, and if the ruleset refuses, the refusal itself appears with
    the override box under it -- asked at the moment it applies, quoting
    what is actually being overridden, instead of standing by empty."""
    targets = [(m.RULESET_ID, lid) for m in rulesets.list_rulesets()
                if "terms" in m.CAPABILITIES for lid in sorted(m.TERM_LISTS)]
    with st.form("addterm", clear_on_submit=True):
        cols = st.columns([3, 3, 4, 1])
        target = cols[0].selectbox("Add to list", targets,
                                    format_func=lambda t: f"{t[0]}.{t[1]}")
        term = cols[1].text_input("Term")
        note = cols[2].text_input("Note", placeholder="why this project uses it")
        with cols[3]:
            st.caption("")
            submitted = st.form_submit_button("Add")
    if submitted and term.strip():
        _submit_term(target, term.strip(), note)

    pending = st.session_state.get("term_refused")
    if not pending:
        return
    st.warning(pending["message"])
    cols = st.columns([4, 1, 1])
    reason = cols[0].text_input("Override reason", key="override_reason",
                                 placeholder="goes on the record beside the term")
    with cols[1]:
        st.caption("")
        if st.button("Override", key="override_go") and reason.strip():
            _submit_term(pending["target"], pending["term"], pending["note"],
                          force=reason.strip())
    with cols[2]:
        st.caption("")
        if st.button("Cancel", key="override_cancel"):
            del st.session_state["term_refused"]
            st.rerun()


def _submit_term(target, term, note, force=False):
    module = rulesets.get_ruleset(target[0])
    try:
        result = module.add_term(target[1], term, note, force=force)
    except Exception as exc:
        st.error(f"Not saved: {exc}")
        return
    if not result.get("ok") and not force:
        st.session_state["term_refused"] = {
            "target": target, "term": term, "note": note,
            "message": result.get("message", "")}
        st.rerun()
    st.session_state.pop("term_refused", None)
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


def _playground_section(probe, full, ruleset_id):
    """Text as if written to the scoped path -- the real gate call.

    Two bugs lived in the ruleset dropdown this used to carry. It could name
    a ruleset the path never routes to, so the answer described a gate call
    that cannot happen. And it never passed a path down, so vocabulary
    resolved against the synthetic free-text name: with a pack bound to
    `docs/*.md` this returned a verdict computed from 0 project terms where
    the gate would have used 187. A playground that can disagree with the
    gate is worse than none -- it is the screen people trust to check."""
    st.subheader("Try it")
    if not ruleset_id:
        st.caption(f"`{probe}` is out of scope, so the gate would not run at "
                   f"all. Point the path box at a file a rule matches.")
        return
    st.caption(f"Linted exactly as the gate would lint `{probe}`: "
               f"**{ruleset_id}**, with that path's own vocabulary.")
    text = st.text_area("Text", height=120, key="playground_text",
                         placeholder="Paste a sentence or a snippet...")
    if not (st.button("Lint it", type="primary", key="lint_btn") and text.strip()):
        return

    ruleset = rulesets.get_ruleset(ruleset_id)
    result = ruleset.lint_and_gate(text, file_path=full)
    blocking = ruleset.blocking_semantic_flags(result["semantic_flags"])
    if blocking:
        st.error(f"Would DENY -- {len(blocking)} flag(s) need a person's judgment")
        for f in blocking:
            st.write(f"- **[{f['kind']}]** {f.get('label') or ''} -- "
                     f"{f['detail'].get('note', '')}")
    elif result["mechanical_violations"]:
        st.warning(f"Would AUTO-FIX -- {len(result['mechanical_violations'])} "
                   f"mechanical violation(s)")
        st.code(ruleset.apply_mechanical_fixes(text, file_path=full))
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
