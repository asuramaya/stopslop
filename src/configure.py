#!/usr/bin/env python3
"""The Configure page: pick a path, and every control over what the gate
does to it is on one screen.

The order of the page is the order of the question. A Path selector
picks a routing rule; the editable first-match-wins table stays visible
under it because rule ORDER is load-bearing and invisible in any view
that only shows the winner; the focused rule's vocabulary packs sit
below the table (_rule_packs_editor). Then the resolved ruleset: the
playground, beside the checks it exercises (_playground); one editable
table of every check with its switch, threshold and action in the row
(_by_check); and the words and extra settings behind the few checks
that have any (_check_contents). The single search box reaches checks
AND every word in every list (_word_matches) -- "is `leverage` banned,
and where" was always a search, never a view.

Every edit applies immediately, the same promise the page makes about
reaching the next gate call. Anything that cannot be read back off the
result (deleting a rule, renaming a glob, removing selected words)
confirms first, and the last write is always undoable, because every
mutation on this page lands in one file (_snapshot / _undo_bar).

Two Streamlit constraints shaped more of this layout than taste did,
and each is documented where it bites: a grid cannot be editable AND
selectable (_routing_section), and a keyed widget outlives the data it
mirrors (the apply-on-change block below, and _undo_bar's key
clearing). The page's own prose is gated by the same product it
configures -- see docs/embedded-prose.md.
"""
import os
import re
import time

import streamlit as st

import rulesets
from core import config as core_config
from core import glossary_packs, history as core_history, terms as core_terms


def relative_time(ts):
    """'2h ago' for a timestamp, '?' for a missing one. Lives here rather
    than dashboard.py because both pages need it and the import only runs
    one way (dashboard imports this module)."""
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


# --- undo: one config file, so one mechanism covers every mutation --------

def _snapshot(project_root, label):
    """Remember the config file exactly as it is, under a human label.

    Deliberately a whole-file snapshot rather than a per-action inverse.
    Every control on this page writes to stopslop.config.json through
    core.config, so one blob restores any of them, and a new write shape
    added later is covered without anyone remembering to write its undo."""
    path = core_config.config_path(project_root)
    before = None
    if os.path.exists(path):
        with open(path) as f:
            before = f.read()
    st.session_state["undo"] = {"label": label, "blob": before, "path": path}


def _undo_bar():
    # A callback cannot render, so a failed write parks its message here.
    error = st.session_state.pop("write_error", None)
    if error:
        st.error(f"Not saved: {error}")

    entry = st.session_state.get("undo")
    if not entry:
        return
    cols = st.columns([6, 1])
    cols[0].caption(f"Last change: {entry['label']}")
    if cols[1].button("Undo", key="undo_btn", width="stretch"):
        if entry["blob"] is None:
            if os.path.exists(entry["path"]):
                os.unlink(entry["path"])
        else:
            with open(entry["path"], "w") as f:
                f.write(entry["blob"])
        del st.session_state["undo"]
        # Drop the widget state for every control that mirrors the config.
        # A keyed widget outlives the value it was showing, so restoring the
        # file alone would leave the toggles and numbers displaying what was
        # just undone -- and the next interaction would write THAT back.
        for key in [k for k in st.session_state
                    if k.startswith(("param::", "pack::", "checks_editor::"))]:
            del st.session_state[key]
        st.toast("Reverted", icon="↩️")
        st.rerun()


def _confirm(key, question, detail=""):
    """A two-press guard for a change that cannot be read back off the
    result. Returns True on the second press.

    Used only where the edit destroys something the screen would then stop
    showing -- a deleted rule, a renamed glob (which takes its pack
    bindings with it), a batch word removal. A toggle or a threshold needs
    no guard: its new value IS the confirmation, visible where you left
    it, and undo covers the rest."""
    pending = st.session_state.get("confirm_key")
    if pending != key:
        if st.button(question, key=f"ask_{key}"):
            st.session_state["confirm_key"] = key
            st.rerun()
        return False
    st.warning(detail or question)
    cols = st.columns([1, 1, 6])
    if cols[0].button("Yes, do it", key=f"yes_{key}", type="primary"):
        del st.session_state["confirm_key"]
        return True
    if cols[1].button("Cancel", key=f"no_{key}"):
        del st.session_state["confirm_key"]
        st.rerun()
    return False


# --- the page -------------------------------------------------------------

def configure_page(repo_root):
    # Runs BEFORE anything that mirrors config state -- an Undo click's own
    # rerun clears stale widget keys inline, inside this call. When a
    # pack-editing multiselect lived in _routing_section (called first,
    # before this moved), it drew with the pre-undo session-state value
    # before the clearing ever ran, so the click undid the FILE correctly
    # but the widget kept showing the old selection until the next,
    # unrelated rerun. Anything below this line is safe to mirror config;
    # anything that would need to run before it is not.
    _undo_bar()
    probe, full, rule = _routing_section(repo_root)
    ruleset_id = rule["ruleset"] if rule else None

    with st.container(border=True):
        _rules_section(repo_root, probe, full, ruleset_id)


def _display_path(probe):
    """The probe path as a human should see it: the stand-in stem goes
    back to being the wildcard it replaced. `__probe__.md` is an internal
    name for fnmatch's benefit; a caption saying "13 checks run on
    __probe__.md" leaks it."""
    return probe.replace("__probe__", "*")


def _synthetic_path_for_glob(glob):
    """A literal path fnmatch would actually match against `glob` -- for
    "Try it" and any pack/context resolution downstream, which need a
    concrete path, not a pattern. Every wildcard segment becomes a fixed
    stand-in; a literal glob (no "*") is already a real path and passes
    through untouched. The same role core.config.SYNTHETIC_TEXT_NAME
    plays for free text with no file at all, generalized to any glob
    instead of hardcoding "*.md"."""
    return glob.replace("*", "__probe__") if "*" in glob else glob


def _routing_section(repo_root):
    """The routing rules, and the one currently focused. Returns (probe,
    full path, rule dict or None).

    Used to be a free-text "Configuring for path" box, resolved against
    the table below to find out anything -- but the table already names
    every real rule directly; typing a path that might not even exist
    was a detour to a fact already on screen. A first cut of this drew a
    SECOND table just to make a row clickable: st.dataframe selects but
    can't edit, st.data_editor edits but can't select, so "pick a rule"
    and "edit a rule" got two separate grids, the same three columns
    rendered twice, one of them inert. A "Path" selectbox does the
    picking instead -- one line, not a second copy of the table -- and
    the real, editable table stays the only table, always visible (rule
    ORDER is load-bearing for first-match-wins, so it's not behind a
    disclosure either)."""
    with st.container(border=True):
        stored = core_config.rule_packs(repo_root)
        if not stored:
            st.caption("No routing rules yet. Add one below.")
            _routing_table(repo_root)
            probe = core_config.SYNTHETIC_TEXT_NAME
            return probe, os.path.join(repo_root, probe), None

        # Same default a fresh page used to open on: whichever rule
        # governs a real file in this repo, not the first row alphabetically.
        default_rule = core_config.matching_rule(
            os.path.join(repo_root, _opening_path(repo_root)), repo_root)
        default_idx = next((i for i, (g, _r, _p) in enumerate(stored)
                             if default_rule and g == default_rule["glob"]), 0)

        labels = [f"{g} → {r or 'out of scope'}" for g, r, _p in stored]
        idx = st.selectbox("Path", range(len(stored)), index=default_idx,
                            format_func=lambda i: labels[i], key="routing_focus")
        glob, ruleset_id, packs = stored[idx]
        rule = {"glob": glob, "ruleset": ruleset_id, "packs": packs}
        probe = _synthetic_path_for_glob(glob)
        full = os.path.join(repo_root, probe)

        _routing_table(repo_root)

        if ruleset_id:
            _rule_packs_editor(repo_root, rule)
        else:
            st.caption("Out of scope. Nothing is checked here.")
    return probe, full, rule


def _rule_packs_editor(repo_root, rule):
    """Which vocabulary packs feed the focused rule's term lists.

    Select the list first, only if the ruleset has more than one that
    takes packs -- most rulesets do (ste100's project_terms, codewatch's
    generic_naming, all five of slopwatch's deny lists), which is exactly
    why this reads TERM_LISTS rather than naming a list: a control that
    only knew about ste100's one would already be wrong for the other
    two. Then the packs actually bound to the chosen list. See the module
    docstring for why this moved here from inside a check's detail view.

    Renders BELOW the routing table, not above it: it used to be the
    second control on the whole page, which handed the rarest operation
    (bulk vocabulary attachment) the best real estate, before a stranger
    had met a check or a word. The label names the focused glob so the
    control cannot be misread as ruleset-wide -- packs bind to one rule."""
    module = rulesets.get_ruleset(rule["ruleset"])
    lists = getattr(module, "TERM_LISTS", {})
    pack_lists = sorted(lid for lid, spec in lists.items() if spec.get("accepts_packs"))
    if not pack_lists:
        st.caption(f"{rule['ruleset']} has no term list that accepts packs.")
        return

    if len(pack_lists) == 1:
        list_id = pack_lists[0]
    else:
        list_id = st.selectbox("Which list", pack_lists,
                                key=f"packlist::{rule['glob']}")

    spec = lists[list_id]
    attachable = sorted(
        p for p in glossary_packs.AVAILABLE_PACKS
        if core_terms.pack_kind_admissible(spec, glossary_packs.AVAILABLE_PACKS[p])[0])
    current = list((rule.get("packs") or {}).get(list_id, []))
    key = f"pack::{rule['glob']}::{list_id}"
    # Name the check this list feeds too, when it differs from the list's
    # own id (ste100's project_terms feeds `vocabulary`, three lists to one
    # check) -- the checks grid below is searchable by check id, not list
    # id, and the two only happen to match for rulesets with 1:1 lists.
    feeds = spec.get("feeds")
    label = f"Packs feeding `{list_id}` on `{rule['glob']}`"
    if feeds and feeds != list_id:
        label += f" (the `{feeds}` check)"
    st.multiselect(
        label, attachable, default=current, key=key,
        placeholder="No packs attached",
        on_change=_rule_packs_changed,
        args=(repo_root, rule["glob"], rule["ruleset"], list_id, key),
        help="Bulk, license-checked vocabulary from a real outside source "
             "-- see NOTICE at the repo root for each pack's source and license.")


def _rule_packs_changed(repo_root, glob, ruleset_id, list_id, key):
    chosen = st.session_state[key]
    _snapshot(repo_root, f"set {list_id} packs on {glob} to "
                          f"{', '.join(chosen) or '(none)'}")
    try:
        spec = rulesets.get_ruleset(ruleset_id).TERM_LISTS[list_id]
        core_config.set_rule_packs(
            repo_root, glob, list_id, chosen,
            known_packs=glossary_packs.AVAILABLE_PACKS,
            admissible=lambda pid: core_terms.pack_kind_admissible(
                spec, glossary_packs.AVAILABLE_PACKS.get(pid, {})))
    except Exception as exc:
        st.session_state["write_error"] = str(exc)


def _opening_path(repo_root):
    """A REAL file to open on, when one is obvious.

    The page used to greet a first-time reader with `__stdin__.md`, a
    synthetic name that means something to this codebase and nothing to a
    person: the whole screen was configured for a file that does not exist.
    The synthetic name is still reachable by typing it, and the help text
    now says what it is for."""
    for candidate in ("README.md", "readme.md"):
        if os.path.exists(os.path.join(repo_root, candidate)):
            return candidate
    return core_config.SYNTHETIC_TEXT_NAME


def _pack_count(rule):
    return sum(len(v) for v in (rule.get("packs") or {}).values())


# --- apply-on-change, done the one way that is safe -----------------------
#
# A keyed Streamlit widget returns SESSION STATE, not a fresh render of the
# data behind it. So the obvious shape for instant save --
#
#     value = st.selectbox(..., key="k")
#     if value != stored: write(value)
#
# -- is a silent-write bug, not a style choice. Whenever the stored value
# changes for any reason the widget did not cause (a different path
# resolving to a different rule, an undo, another process editing the
# config), the stale widget value differs from the new stored one and the
# write fires with nobody having touched anything. It cost this repo a real
# corruption: the scope box carried "slopwatch" across a path change and
# silently re-routed *.md away from ste100, in the config file, on page
# load. `on_change` fires only on genuine interaction, which is the whole
# difference. Callbacks also must not call st.rerun() -- Streamlit reruns
# after them anyway.




def _routing_table(repo_root):
    st.caption("First match wins; order matters.")
    stored = core_config.rule_packs(repo_root)
    edited = st.data_editor(
        [{"glob": g, "ruleset": r or "", "packs": _pack_count({"packs": p})}
         for g, r, p in stored],
        num_rows="dynamic", width="stretch", key="routing_editor",
        column_config={
            "glob": st.column_config.TextColumn("glob", required=True),
            "ruleset": st.column_config.SelectboxColumn(
                "ruleset", options=[""] + [m.RULESET_ID for m in rulesets.list_rulesets()],
                help="Empty means out of scope entirely (like .claude/*)."),
            "packs": st.column_config.NumberColumn(
                "packs", disabled=True, width="small",
                help="Vocabulary bound to this rule. Attach and detach these "
                      "in the packs control under this table -- the count is "
                      "shown here so a glob edit cannot silently drop them."),
        })

    incoming = [{"glob": r["glob"], "ruleset": r["ruleset"] or None}
                for r in edited if r.get("glob")]
    if incoming == [{"glob": g, "ruleset": r} for g, r, _ in stored]:
        return

    kept = {r["glob"] for r in incoming}
    lost = {g: sum(len(v) for v in p.values()) for g, _, p in stored
            if p and g not in kept}
    gone = [g for g, _, _ in stored if g not in kept]
    if not gone:
        _snapshot(repo_root, "edited routing")
        try:
            core_config.save_rules(repo_root, incoming, rulesets)
            st.rerun()
        except Exception as exc:
            st.error(f"Not saved: {exc}")
        return

    # A removed glob may be a delete OR a rename -- indistinguishable from
    # here, and both take the rule's pack bindings with them, because a
    # glob IS a rule's identity. Say exactly what goes.
    detail = f"These rules go: {', '.join(f'`{g}`' for g in gone)}."
    if lost:
        detail += (" That also drops " +
                   ", ".join(f"{n} pack binding(s) on `{g}`" for g, n in lost.items()) +
                   ". Re-attach them inside the check that uses them.")
    if _confirm("routing_del", f"Apply routing change ({len(gone)} rule(s) removed)",
                 detail):
        _snapshot(repo_root, f"removed {len(gone)} routing rule(s)")
        try:
            core_config.save_rules(repo_root, incoming, rulesets)
            st.rerun()
        except Exception as exc:
            st.error(f"Not saved: {exc}")


# --- Rules: every check, with its parameter and its words inside it -------

def _rules_section(repo_root, probe, full, ruleset_id):
    if not ruleset_id:
        # Out of scope: nothing below applies. Rendering the checks
        # machinery would also crash -- get_ruleset(None) raises.
        st.info("This path is out of scope, so nothing below runs on it.")
        return
    # The playground sits WITH the checks it exercises, not at the bottom
    # of the page below the add-word form, where the only element that
    # demonstrates the system working was the last thing anyone found.
    # An expander rather than an open panel: visible and one click away
    # without asking for text before showing any state.
    with st.expander("Try it: paste text, see what the gate does"):
        _playground(repo_root, probe, full, ruleset_id)
    _by_check(repo_root, probe, full, ruleset_id)



def _check_rows(ruleset_id):
    """Every check of the ruleset governing the focused path -- and only
    that ruleset's.

    This used to return all 43 checks fleet-wide, sorting the focused
    ruleset first and dimming the rest with a leading dot, which meant
    two thirds of the rows on screen did not apply to the path the whole
    page is configured for. It needed a `ruleset` column, a ruleset
    filter, a dimming convention and a "Runs on files routed to X, not on
    this path" caption to explain itself -- four devices whose only job
    was to undo the confusion of showing the other rows at all. The Path
    selector at the top already picks the ruleset; changing it is how you
    reach another one."""
    module = rulesets.get_ruleset(ruleset_id)
    if "checks" not in module.CAPABILITIES:
        return module, []
    # One shape for every ruleset now: each check carries its own
    # {threshold, action}, plus any extra per-check numbers the ruleset
    # declares (ste100's length carries its two word limits) under
    # "params" -- rendered in the check's own detail, never as a column
    # shared across checks that don't have them.
    check_config = module.list_check_config() if "check_config" in module.CAPABILITIES else {}
    lists = getattr(module, "TERM_LISTS", {})
    rows = []
    for check_id, meta in sorted(module.list_checks().items()):
        spec = check_config.get(check_id)
        rows.append({
            "module": module, "check": check_id, "ruleset": module.RULESET_ID,
            "catches": meta["catches"], "instead": meta["instead"],
            "enabled": meta["enabled"],
            "threshold": spec["threshold"] if spec else None,
            "action": spec["action"] if spec else None,
            "params": (spec.get("params", {}) if spec else {}),
            # Lists this check owns, by the list's own declaration.
            # ste100 maps three lists onto one check, so matching on
            # the id would leave `vocabulary` looking wordless.
            "lists": [lid for lid, spec in lists.items()
                      if spec.get("feeds") == check_id],
        })
    return module, rows




def _by_check(repo_root, probe, full, ruleset_id):
    """One editable table: every check of this path's ruleset, its on/off
    switch, and its own numbers, all in the row.

    This was master/detail -- a read-only grid, and a pane below carrying
    the toggle and any settings for whichever row you clicked. Streamlit
    forces that shape on anything needing both selection and editing (see
    _routing_section for the constraint), and the cost landed exactly
    where it hurt: 34 of the fleet's 44 checks have NOTHING inside them
    but an on/off switch, so four rows in five made you click into a pane
    that was empty except for the toggle you came for. Worse, the pane's
    toggle sat under a table whose leftmost column was Streamlit's own
    selection checkbox -- two checkbox-shaped controls for one row, the
    inert-looking one being the real selector.

    Editing wins the trade. `on` is a real checkbox in the row, each
    numeric setting is a cell, and nothing is one click away that used to
    be. What genuinely cannot be a cell -- a check's word LISTS, and its
    own extra params (length's word limits) -- moves below under a
    selector naming only the checks that have any, so the pane appears
    for the rows it has content for instead of all of them."""
    module, rows = _check_rows(ruleset_id)
    if not rows:
        st.caption(f"{ruleset_id} declares no checks.")
        return

    off = sum(1 for r in rows if not r["enabled"])
    st.caption(f"{len(rows)} checks run on `{_display_path(probe)}`"
               + (f", {off} turned off." if off else "."))
    needle = st.text_input(
        "Search", key="rules_q",
        placeholder="a check, or any word in any list",
        help="Matches checks by name and description, and every word in "
             "every ruleset's lists -- ste100's whole dictionary lives "
             "under one check, so \"is `leverage` banned\" is a word "
             "search, not a row in this table.").strip().lower()
    shown = [r for r in rows
             if not needle or needle in r["check"].lower()
             or needle in r["catches"].lower() or needle in r["instead"].lower()]
    if not shown:
        st.caption("No check matches.")
        _word_matches(repo_root, full, needle)
        return

    # threshold and action are real settings on EVERY row of every
    # ruleset now, so a NumberColumn's blank-renders-as-"None" problem
    # (the reason older sparse columns used TextColumn) no longer
    # applies; there is no blank cell left to render badly.
    table, config = [], {
        "on": st.column_config.CheckboxColumn("on", width="small"),
        "check": st.column_config.TextColumn("check", width="medium", disabled=True),
        "what it catches": st.column_config.TextColumn(
            "what it catches", width="large", disabled=True),
        "threshold": st.column_config.NumberColumn(
            "threshold", width="small", min_value=1, step=1,
            help="How many times this check has to fire in a document "
                 "before it counts as triggered."),
        "action": st.column_config.SelectboxColumn(
            "action", width="small", options=["warn", "block"],
            help="warn: shown, never denies a write by itself. block: "
                 "denies the write once this check's own threshold above "
                 "is reached."),
        "last fired": st.column_config.TextColumn(
            "last fired", width="small", disabled=True,
            help="The newest gate event in this repo where this check "
                 "flagged something. Blank means it has never fired here."),
    }

    fired = _last_fired(repo_root, ruleset_id)
    for r in shown:
        table.append({"on": r["enabled"], "check": r["check"],
                       "what it catches": r["catches"],
                       "threshold": r["threshold"], "action": r["action"],
                       "last fired": (relative_time(fired[r["check"]])
                                       if r["check"] in fired else "")})

    # Keyed per ruleset: switching Path swaps every row underneath, and a
    # shared key would carry the previous ruleset's edits onto whatever
    # rows happen to land in the same positions.
    edited = st.data_editor(
        table, width="stretch", hide_index=True, height=380, num_rows="fixed",
        key=f"checks_editor::{ruleset_id}", column_config=config,
        column_order=["on", "check", "what it catches",
                      "threshold", "action", "last fired"])
    _apply_check_edits(repo_root, module, shown, table, edited)
    _check_contents(repo_root, full, shown, ruleset_id)
    _word_matches(repo_root, full, needle)


def _last_fired(repo_root, ruleset_id):
    """{check_id: ts} of the newest gate event in this repo naming each
    check -- the Watch page's data, joined into the table where tuning
    happens, so "the gate just denied something, which row was it" needs
    no page switch and no remembered check id.

    Reads the log fresh every rerun, the same never-cache treatment every
    config read here gets; the log is small and append-only. Revisit with
    an mtime-keyed cache only if it measurably drags."""
    events = core_history.read_history_deduped(
        core_history.history_log_path(repo_root))
    out = {}
    for e in events:
        if e.get("ruleset") != ruleset_id:
            continue
        ts = e.get("ts", 0)
        for kind in e.get("kinds") or []:
            if ts > out.get(kind, 0):
                out[kind] = ts
    return out



def check_config_edits(rows, before, after):
    """(toggles, check_config_changes, error) for a check_config-capable
    ruleset's table -- threshold and action are real per-CHECK settings
    now, not a shared ruleset-wide options dict, so a change is keyed by
    check id rather than by option name. Same pure-and-separate-from-
    writing shape as check_edits, and the same reason (see that
    function's own docstring); `check_config_changes` is
    {check_id: {"threshold": N, "action": ...}}, only the fields that
    actually moved on that row."""
    toggles, changes = {}, {}
    for row, was, now in zip(rows, before, after):
        if bool(now.get("on")) != bool(was["on"]):
            toggles[row["check"]] = bool(now["on"])
        row_changes = {}
        now_threshold = now.get("threshold")
        # None means the cell was left alone or cleared -- never write a
        # "no threshold" that has no meaning here; the check keeps
        # whatever it already had.
        if now_threshold is not None:
            try:
                now_threshold = int(now_threshold)
            except (TypeError, ValueError):
                return {}, {}, (f"{row['check']}: threshold must be a whole "
                                 f"number, not {now_threshold!r}")
            if now_threshold < 1:
                return {}, {}, f"{row['check']}: threshold must be at least 1"
            if now_threshold != was["threshold"]:
                row_changes["threshold"] = now_threshold
        now_action = now.get("action")
        if now_action and now_action != was["action"]:
            row_changes["action"] = now_action
        if row_changes:
            changes[row["check"]] = row_changes
    return toggles, changes, None


def _apply_check_edits(repo_root, module, rows, before, after):
    """Write whatever check_config_edits found, and nothing else. Only
    genuine differences are written, so a rerun triggered by anything
    else on the page (a Path change, an undo) writes nothing."""
    toggles, changes, error = check_config_edits(rows, before, after)
    if error:
        st.session_state["write_error"] = error
        return
    if not toggles and not changes:
        return

    labels = ([f"{'enabled' if on else 'disabled'} {c}" for c, on in toggles.items()]
              + [f"set {check_id} {field} to {value}"
                 for check_id, fields in changes.items()
                 for field, value in fields.items()])
    _snapshot(repo_root, "; ".join(labels))
    try:
        if toggles:
            module.set_checks_enabled(toggles)
        for check_id, fields in changes.items():
            module.set_check_config(check_id, **fields)
    except Exception as exc:
        st.session_state["write_error"] = str(exc)
        return
    st.rerun()


def _check_contents(repo_root, full, rows, ruleset_id):
    """The words and extra settings behind a check, for the checks that
    have any.

    Every row used to open a pane like this, and for most it held nothing
    but the on/off toggle -- now a cell in the row (see _by_check for the
    numbers). So the selector lists only the checks with something
    actually inside, and with none it does not render at all."""
    have = [r for r in rows if r["lists"] or r["params"]]
    if not have:
        return

    st.divider()
    if len(have) == 1:
        # A selectbox offering one choice is a control that does nothing.
        row = have[0]
        st.caption(f"Words and settings: `{row['check']}` is the only one "
                   f"of these checks with any.")
    else:
        labels = {r["check"]: f"{r['check']}: " + ", ".join(
            filter(None, [f"{len(r['lists'])} word list(s)" if r["lists"] else "",
                          ", ".join(n.replace("_", " ") for n in r["params"])]))
            for r in have}
        picked = st.selectbox(
            f"Words and settings ({len(have)} of these {len(rows)} checks have any)",
            [r["check"] for r in have], key=f"check_contents::{ruleset_id}",
            format_func=lambda c: labels[c])
        row = next(r for r in have if r["check"] == picked)

    # One line, whole story: what the check catches, then the remedy --
    # the remedy used to float alone as "Instead: ..." with nothing on
    # screen saying instead of WHAT.
    st.caption(f"{row['catches']}. Instead, {row['instead']}.")
    for name, info in row["params"].items():
        _param_control(repo_root, row, name, info)
    for list_id in row["lists"]:
        _term_list_block(repo_root, row, list_id, full)


def _param_control(repo_root, row, name, info):
    """A check's own extra number (ste100 length's two word limits) --
    per-check config, written through the same set_check_config path as
    the threshold/action cells in the table above."""
    cols = st.columns([2, 6])
    key = f"param::{row['ruleset']}::{row['check']}::{name}"
    cols[0].number_input(name.replace("_", " "), value=int(info["value"]),
                          min_value=1, step=1, key=key,
                          on_change=_param_changed,
                          args=(repo_root, row["module"], row["check"], name, key))
    with cols[1]:
        st.caption("")
        st.caption(f"built-in default: {info['default']}")


def _param_changed(repo_root, module, check_id, name, key):
    value = int(st.session_state[key])
    _snapshot(repo_root, f"set {check_id} {name.replace('_', ' ')} to {value}")
    try:
        module.set_check_config(check_id, **{name: value})
    except Exception as exc:
        st.session_state["write_error"] = str(exc)




def _resolve_counts(repo_root, module, list_id, full):
    layers = core_terms.resolve(module.TERM_LISTS[list_id], repo_root,
                                 module.RULESET_ID, list_id, file_path=full)
    counts = {}
    for term in layers["effective"]:
        if term in layers["project"]:
            source = "yours"
        elif term in layers["packs"]:
            source = layers["packs"][term].get("pack", "pack")
        else:
            source = "built-in"
        counts[source] = counts.get(source, 0) + 1
    return counts


def _term_list_block(repo_root, row, list_id, full):
    """A check's words: where they come from, what they are, how to add.

    The sources summary, the source filter and the suppressed list were
    three separate views of one idea, spread across a section. Here the
    summary IS the filter (click a source), and a suppressed word is a
    word with a state rather than a collection of its own. Attaching or
    detaching a whole PACK is not here -- see _rule_packs_editor and the
    module docstring for why that moved to the routing rule itself; a
    source labelled "pack" below is still informational, naming where a
    word came from even though this is no longer where you'd change it."""
    module = row["module"]
    spec = module.TERM_LISTS[list_id]
    layers = core_terms.resolve(spec, repo_root, module.RULESET_ID, list_id,
                                 file_path=full)
    packs = set(glossary_packs.AVAILABLE_PACKS)
    # Name the list. A check can own more than one -- ste100's `vocabulary`
    # stacks three, an allow list, a deny list and the project's own -- and
    # three unlabelled blocks of words read as one repeated widget. One
    # statement of each fact: the label (the id lives in its tooltip, for
    # cross-reference with the packs control), the count, and what being
    # on the list DOES, in plain words rather than an ALLOW/DENY tag the
    # sentence right after it restated.
    polarity = spec.get("polarity")
    st.markdown(f"**{spec.get('label') or list_id}**: "
                f"{len(layers['effective'])} words; "
                + ("a word here stops being flagged." if polarity == "allow"
                   else "a word here gets flagged."),
                help=f"list id: `{list_id}`")

    counts = _resolve_counts(repo_root, module, list_id, full)
    key = f"{module.RULESET_ID}.{list_id}"
    active = st.session_state.get(f"srcfilter_{key}")
    suppressed = core_terms.suppressed_terms(repo_root, module.RULESET_ID, list_id)
    # A filter over one source filters nothing: skip the buttons unless
    # there are at least two places a word here can come from.
    if len(counts) + (1 if suppressed else 0) > 1:
        for source, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
            cols = st.columns([3, 1])
            selected = active == source
            if cols[0].button(f"{'▸ ' if selected else ''}{source}  ({n})",
                               key=f"src_{key}_{source}", width="stretch"):
                st.session_state[f"srcfilter_{key}"] = None if selected else source
                st.rerun()
            if source in packs:
                cols[1].caption("pack")

        if suppressed:
            cols = st.columns([3, 1])
            selected = active == "suppressed"
            if cols[0].button(f"{'▸ ' if selected else ''}suppressed  ({len(suppressed)})",
                               key=f"src_{key}_suppressed", width="stretch"):
                st.session_state[f"srcfilter_{key}"] = None if selected else "suppressed"
                st.rerun()
            cols[1].caption("removed")
    else:
        active = None       # a filter that survived its second source

    _word_table(repo_root, module, list_id, layers, suppressed, active, key)
    _add_vocabulary(repo_root, module, list_id, spec)
    # A refusal (ste100 validating against the real standard) surfaces
    # right under the Add control that caused it -- it used to render
    # inside the playground at the bottom of the page, a screen away from
    # the word it was refusing. Guarded to this list so a check with
    # several lists shows the prompt once, under the right one.
    pending = st.session_state.get("refused")
    if (pending and pending["list"] == list_id
            and pending["ruleset"] == module.RULESET_ID):
        _override_prompt(repo_root)


def _word_table(repo_root, module, list_id, layers, suppressed, active, key):
    if active == "suppressed":
        rows = [{"term": t, "source": "suppressed", "note": ""}
                for t in sorted(suppressed)]
    else:
        rows = []
        for term in sorted(layers["effective"]):
            if term in layers["project"]:
                source = "yours"
            elif term in layers["packs"]:
                source = layers["packs"][term].get("pack", "pack")
            else:
                source = "built-in"
            if active and source != active:
                continue
            rows.append({"term": term, "source": source,
                          "note": layers["effective"][term].get("note", "") or ""})
    if not rows:
        st.caption("No words from that source.")
        return

    event = st.dataframe(rows, width="stretch", hide_index=True, height=220,
                          on_select="rerun", selection_mode="multi-row",
                          key=f"words_{key}")
    chosen = [rows[i] for i in event.selection.rows]
    if not chosen:
        return
    if active == "suppressed":
        if st.button(f"Restore {len(chosen)}", key=f"restore_{key}"):
            _snapshot(repo_root, f"restored {len(chosen)} word(s) to {list_id}")
            for r in chosen:
                module.add_term(list_id, r["term"])
            st.rerun()
        return
    not_yours = [r for r in chosen if r["source"] != "yours"]
    detail = (f"{len(chosen)} word(s) go. "
              + (f"{len(not_yours)} of them come from a built-in list or a "
                 f"pack, so they are suppressed rather than deleted and stay "
                 f"restorable." if not_yours else "All are your own, so they are deleted."))
    if _confirm(f"rm_{key}", f"Remove {len(chosen)} selected word(s)", detail):
        _snapshot(repo_root, f"removed {len(chosen)} word(s) from {list_id}")
        for r in chosen:
            try:
                module.remove_term(list_id, r["term"])
            except Exception as exc:
                st.error(f"{r['term']}: {exc}")
        st.rerun()


def _add_vocabulary(repo_root, module, list_id, spec):
    """Add a single word to a term list.

    Used to also attach a whole pack from this same control -- adding a
    word and attaching a pack read as the same verb at different scale,
    but they act on different things (a list vs. a routing rule), and
    packs live on the routing rule now. See _rule_packs_editor."""
    if not spec.get("accepts_additions", True):
        # Offering a control that always refuses is worse than offering
        # none. ste100's two dictionary lists are published reference data;
        # removal and restore stay available on the rows above.
        st.caption("This list takes no new words; it is published reference "
                   "data. Remove a word above to stop using it here, or add "
                   "your own to the project list.")
        return
    cols = st.columns([3, 3, 1])
    entry = cols[0].text_input(
        "Add a word", key=f"add_{module.RULESET_ID}_{list_id}",
        help="Type a single word to register it here.")
    note = cols[1].text_input("Note", key=f"note_{module.RULESET_ID}_{list_id}",
                               placeholder="why this project uses it")
    with cols[2]:
        st.caption("")
        if st.button("Add", key=f"addbtn_{module.RULESET_ID}_{list_id}") and entry.strip():
            _add_word(repo_root, module, list_id, entry.strip(), note)


def _add_word(repo_root, module, list_id, term, note):
    _snapshot(repo_root, f"added '{term}' to {list_id}")
    try:
        result = module.add_term(list_id, term, note)
    except Exception as exc:
        st.error(f"Not saved: {exc}")
        return
    if not result.get("ok"):
        # Only ste100 validates against a real external standard, so this
        # is the one place an override can even arise. Ask at the moment it
        # applies, quoting the refusal, rather than keeping a permanently
        # visible box that is dead for eight of the nine lists.
        st.session_state["refused"] = {
            "ruleset": module.RULESET_ID, "list": list_id, "term": term,
            "note": note, "message": result.get("message", "")}
    st.rerun()


def _override_prompt(repo_root):
    pending = st.session_state.get("refused")
    if not pending:
        return
    st.warning(pending["message"])
    cols = st.columns([4, 1, 1])
    reason = cols[0].text_input("Override reason", key="override_reason",
                                 placeholder="goes on the record beside the word")
    with cols[1]:
        st.caption("")
        if st.button("Override", key="override_go") and reason.strip():
            module = rulesets.get_ruleset(pending["ruleset"])
            _snapshot(repo_root, f"force-added '{pending['term']}'")
            module.add_term(pending["list"], pending["term"], pending["note"],
                             force=reason.strip())
            del st.session_state["refused"]
            st.rerun()
    with cols[2]:
        st.caption("")
        if st.button("Cancel", key="override_cancel"):
            del st.session_state["refused"]
            st.rerun()


# --- word search: the answer a check-keyed table cannot give --------------

def _word_matches(repo_root, full, needle):
    """Words matching the search, across every ruleset's lists.

    "Is `leverage` banned, and where" is a real question a check-keyed
    table cannot answer -- ste100's 2830 words sit under ONE check while
    codewatch's 12 sit under another. This used to be a whole second view
    behind a "by check / all words" mode pill; browsing 2830 rows was
    inventory, not a control panel, but SEARCHING them is the real use,
    so the flat table now appears only when the one search box matches
    words. Selection keeps the remove/restore operations the old view
    carried; the CLI's terms listing remains the way to dump everything."""
    if not needle:
        return
    rows = core_terms.term_index(rulesets, repo_root, file_path=full)
    for row in rows:
        row["list"] = f"{row['ruleset']}.{row['list']}"
    for row in core_terms.suppressed_index(rulesets, repo_root):
        rows.append({"term": row["term"], "ruleset": row["ruleset"],
                      "list": f"{row['ruleset']}.{row['list']}",
                      "source": "suppressed", "polarity": "", "note": ""})
    hits = [r for r in rows
            if needle in r["term"].lower() or needle in r["note"].lower()]
    if not hits:
        return

    st.caption(f"{len(hits)} matching word(s), in every ruleset's lists "
               f"project-wide -- the list column says which gate each one "
               f"belongs to.")
    event = st.dataframe(
        [{k: r[k] for k in ("term", "list", "source", "note")} for r in hits],
        width="stretch", hide_index=True, height=min(420, 40 + 35 * len(hits)),
        on_select="rerun", selection_mode="multi-row", key="word_matches")
    chosen = [hits[i] for i in event.selection.rows]
    if not chosen:
        return

    restore = [r for r in chosen if r["source"] == "suppressed"]
    remove = [r for r in chosen if r["source"] != "suppressed"]
    if restore and st.button(f"Restore {len(restore)}", key="aw_restore"):
        _snapshot(repo_root, f"restored {len(restore)} word(s)")
        for r in restore:
            rulesets.get_ruleset(r["ruleset"]).add_term(r["list"].split(".", 1)[1],
                                                         r["term"])
        st.rerun()
    if remove and _confirm("aw_rm", f"Remove {len(remove)} selected word(s)",
                            "A built-in or pack word is suppressed rather than "
                            "deleted, and stays restorable."):
        _snapshot(repo_root, f"removed {len(remove)} word(s)")
        for r in remove:
            try:
                rulesets.get_ruleset(r["ruleset"]).remove_term(
                    r["list"].split(".", 1)[1], r["term"])
            except Exception as exc:
                st.error(f"{r['term']}: {exc}")
        st.rerun()


# --- Try it ---------------------------------------------------------------

def _playground(repo_root, probe, full, ruleset_id):
    """Text as if written to the scoped path -- the real gate call.

    Rendered inside the Try-it expander in _rules_section, which guards
    the out-of-scope case before this is ever reached. No title of its
    own: the expander carries it, and the deny line directly above
    already names the ruleset this lints with."""
    st.caption(f"Linted exactly as the gate would lint `{_display_path(probe)}`, "
               f"with that path's own vocabulary.")
    text = st.text_area("Text", height=120, key="playground_text",
                         placeholder="Paste a sentence or a snippet...")
    if not (st.button("Lint it", type="primary", key="lint_btn") and text.strip()):
        return

    ruleset = rulesets.get_ruleset(ruleset_id)
    result = ruleset.lint_and_gate(text, file_path=full)
    blocking = ruleset.blocking_semantic_flags(result["semantic_flags"])
    if blocking:
        st.error(f"Would DENY: {len(blocking)} flag(s) need a person's judgment")
        # Same per-flag format the hook's own deny message uses -- and no
        # bolded [tag] opening each item, which is slopwatch's own
        # bold_bullet_lead pattern, caught here by the dogfooding pass.
        for f in blocking:
            note = f['detail'].get('note', '')
            st.write(f"- [{f['kind']}] {f.get('label') or ''}"
                     + (f": {note}" if note else ""))
    elif result["mechanical_violations"]:
        st.warning(f"Would AUTO-FIX: {len(result['mechanical_violations'])} "
                   f"mechanical violation(s)")
        st.code(ruleset.apply_mechanical_fixes(text, file_path=full))
    else:
        st.success("Would PASS unchanged")
    non_blocking = [f for f in result["semantic_flags"] if f not in blocking]
    if non_blocking:
        with st.expander(f"{len(non_blocking)} non-blocking note(s)"):
            for f in non_blocking:
                st.write(f"- [{f['kind']}] {f.get('label') or ''}")
