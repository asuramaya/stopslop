#!/usr/bin/env python3
"""The Configure page: what happens to this file?

One path at the top, and everything below is an attribute of that path's
ruleset. Three sections, not six, because the previous six were not six
CONCEPTS -- they were one concept, split by which config-file key happened
to store each piece of it.

A check can have an on/off switch, a numeric parameter, and a word list.
Those lived in `Checks`, `Thresholds` and `Terms` respectively, so
understanding one check (`filler_verb`, say) meant reading a row in one
section, scrolling past a second, and filtering a third -- with nothing on
screen connecting them. `slopwatch.em_dash_threshold` is consumed inside
the `em_dash_cluster` check and nowhere else; six checks ARE term lists,
under the same id, listed twice in two disconnected tables. Now a check is
one row, and its parameter and its words are inside it.

What that split was hiding entirely: the deny policy. The page said which
checks fire and which words are known, and never what BLOCKS a write --
the one thing the product exists to do. `block_flag_count_threshold` was a
row in a table called Thresholds, between two unrelated numbers, and two
checks in the fleet (slopwatch's em_dash_cluster, codewatch's
swallowed_exception) deny on their own while rendering identically to
every other row. Each ruleset now states its own policy (DENY_POLICY) and
the rows that deny alone say so.

Packs attach to a ROUTING RULE, not to a check. That used to mean a
control buried inside whichever check happened to read the list a pack
feeds -- a remnant of ste100 being the only ruleset, with exactly one
pack-eligible list, when that placement was still one hop from "the rule
this pack is actually bound to." Once other rulesets and other lists
existed the hop stopped being obvious. A pack is bulk vocabulary bound to
a PATH (which text it covers), and the routing table is where paths and
their rules live -- so packs are edited where the rule is focused, not
inside whichever check happens to consume the words.

One thing is deliberately NOT folded: the full routing table stays
visible with the focused rule, because rule ORDER is load-bearing (first
match wins) and order is invisible in a view that only shows the winner.
The flat all-words view is no longer a mode of its own -- "is this word
banned, and where" was always a SEARCH, so the one search box now reaches
every word in every list, and the old mode pill is gone (_word_matches).

The checks table is EDITABLE, and shows one ruleset -- the one governing
the focused path. It was a read-only grid over all 43 fleet checks, with
a detail pane below carrying the toggle and settings for the selected
row. Both halves of that were wrong. Showing every ruleset's checks meant
two thirds of the rows did not apply to the path the page is configured
for, and needed a ruleset column, a ruleset filter, a dimming convention
and an explanatory caption to undo the confusion of showing them. And
34 of those 43 checks hold NOTHING but an on/off switch, so the pane was
empty-but-for-the-toggle four times in five. The switch and every numeric
setting are cells now; only word lists and set-valued settings, which
have no cell shape, remain below -- reachable for the 9 checks that have
them, absent for the rest.

Every edit applies immediately -- the same promise the page makes about
reaching the next gate call. Anything that cannot be inferred back from
the result (deleting a rule, renaming a glob, removing selected words)
confirms first, and the last write is always undoable, because every
mutation on this page lands in one file.
"""
import os
import re
import time

import streamlit as st

import rulesets
from core import config as core_config
from core import flags as core_flags
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
                    if k.startswith(("opt::", "pack::", "checks_editor::"))]:
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
            st.caption("Out of scope — nothing is checked here.")
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


def _option_changed(repo_root, module, name, key):
    raw = st.session_state[key]
    # number_input's own value can arrive as a float even with step=1;
    # multiselect already returns the list a choice-option needs untouched.
    value = int(raw) if isinstance(raw, (int, float)) else raw
    _snapshot(repo_root, f"set {module.RULESET_ID}.{name} to {value}")
    try:
        module.set_options({name: value})
    except Exception as exc:
        st.session_state["write_error"] = str(exc)


def _routing_table(repo_root):
    st.caption("First match wins — order matters.")
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
    _deny_policy(repo_root, ruleset_id)
    if not ruleset_id:
        # Out of scope: the info line above said it all. Rendering the
        # checks machinery would also crash -- get_ruleset(None) raises.
        return
    # The playground sits WITH the checks it exercises, not at the bottom
    # of the page below the add-word form, where the only element that
    # demonstrates the system working was the last thing anyone found.
    # An expander rather than an open panel: visible and one click away
    # without asking for text before showing any state.
    with st.expander("Try it — paste text, see what the gate does"):
        _playground(repo_root, probe, full, ruleset_id)
    _by_check(repo_root, probe, full, ruleset_id)


def _deny_policy(repo_root, ruleset_id):
    """The deny sentence, with the number in it AS the control.

    A ruleset's options split in two by WHO owns them. A check's own
    parameter (ste100's procedure_word_limit, slopwatch's
    em_dash_threshold) is declared in CHECK_OPTIONS and edited inside
    that check's row. What is left over belongs to the deny policy
    itself -- and it used to render three times in a vertical stack: as
    a number formatted into this sentence, as a raw snake_case label,
    and as a spinner under both, with the sentence itself opening
    "denies a write: A write is denied ...". One statement now: a
    policy-level option named in the text becomes an inline control at
    exactly that spot, so the threshold appears once on the whole page.
    A policy option the text does not name still gets a plain control
    row below. Which options are policy-level is derived -- every option
    no check claims -- never a hardcoded name, so a ruleset adding a
    second policy-level number is covered on arrival."""
    if not ruleset_id:
        st.info("This path is out of scope, so nothing below runs on it.")
        return
    module = rulesets.get_ruleset(ruleset_id)
    policy = getattr(module, "DENY_POLICY", None)
    if not policy:
        return
    options = core_flags.display_options(module)
    owned = {n for names in getattr(module, "CHECK_OPTIONS", {}).values()
             for n in names}
    declared = module.list_options() if "options" in module.CAPABILITIES else {}
    policy_opts = {n: i for n, i in declared.items() if n not in owned}
    row = {"ruleset": ruleset_id, "module": module}

    text = policy["text"]
    inline = [n for n in policy_opts if ("{%s}" % n) in text]
    lead = f"🚫 **{ruleset_id} denies a write** "
    if not inline:
        try:
            text = text.format(**options)
        except KeyError as missing:
            st.caption(f"(policy text names an unknown option {missing})")
        st.markdown(lead + text)
    else:
        pattern = "|".join("\\{%s\\}" % re.escape(n) for n in inline)
        with st.container(horizontal=True, vertical_alignment="center"):
            for piece in re.split(f"({pattern})", text):
                if piece.startswith("{") and piece[1:-1] in policy_opts:
                    name = piece[1:-1]
                    _inline_policy_control(repo_root, row, name,
                                            policy_opts[name])
                    continue
                try:
                    piece = piece.format(**options)
                except KeyError as missing:
                    st.caption(f"(policy text names an unknown option {missing})")
                if lead or piece.strip():
                    st.markdown(lead + piece)
                lead = ""

    for name, info in policy_opts.items():
        if name not in inline:
            _option_control(repo_root, row, name, info)


def _inline_policy_control(repo_root, row, name, info):
    """A policy option named in the deny sentence, rendered as the number
    in that sentence -- the only place its value appears. The sentence is
    the label, so the widget's own is collapsed; the option's name and
    its built-in default live in the tooltip, off the screen."""
    key = f"opt::{row['ruleset']}::{name}"
    st.number_input(
        name, value=int(info["value"]), step=1, key=key, width=90,
        label_visibility="collapsed",
        on_change=_option_changed, args=(repo_root, row["module"], name, key),
        help=f"{name.replace('_', ' ')} — built-in default {info['default']}")


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
    options = ({n: i for n, i in module.list_options().items()}
               if "options" in module.CAPABILITIES else {})
    blocks_alone_at = getattr(module, "DENY_POLICY", {}).get("blocks_alone_at", {})
    owned = getattr(module, "CHECK_OPTIONS", {})
    lists = getattr(module, "TERM_LISTS", {})
    rows = []
    for check_id, meta in sorted(module.list_checks().items()):
        rows.append({
            "module": module, "check": check_id, "ruleset": module.RULESET_ID,
            "catches": meta["catches"], "instead": meta["instead"],
            "enabled": meta["enabled"],
            "blocks_alone_at": blocks_alone_at.get(check_id),
            # A check's own parameter, from the ruleset's own
            # declaration -- the link the separate Thresholds table
            # never drew. Never inferred from the names: see
            # slopwatch's CHECK_OPTIONS for why.
            "options": {n: options[n] for n in owned.get(check_id, ())
                        if n in options},
            # Lists this check owns, by the list's own declaration.
            # ste100 maps three lists onto one check, so matching on
            # the id would leave `vocabulary` looking wordless.
            "lists": [lid for lid, spec in lists.items()
                      if spec.get("feeds") == check_id],
        })
    return module, rows


def _numeric_option_columns(rows):
    """Option names any check in this ruleset carries, in declaration
    order -- one table column each.

    Sparse on purpose: `procedure_word_limit` is blank for the twelve
    ste100 checks that have no word limit, and that blankness is the
    honest answer to "what can I tune on this row" -- most rules are
    binary (a sentence either is passive or it is not) and have no number
    to set. Only a number-valued option becomes a column; a set-valued
    one (ste100's excluded_vocab_types) has no NumberColumn shape and
    stays in the detail below."""
    names = []
    for row in rows:
        for name, info in row["options"].items():
            if "choices" not in info and name not in names:
                names.append(name)
    return names


def _by_check(repo_root, probe, full, ruleset_id):
    """One editable table: every check of this path's ruleset, its on/off
    switch, and its own numbers, all in the row.

    This was master/detail -- a read-only grid, and a pane below carrying
    the toggle and any settings for whichever row you clicked. Streamlit
    forces that shape on anything needing both selection and editing
    (st.dataframe selects but cannot edit; st.data_editor edits but
    cannot select, still true in 1.60), and the cost landed exactly where
    it hurt: 34 of the fleet's 43 checks have NOTHING inside them but an
    on/off switch, so four rows in five made you click into a pane that
    was empty except for the toggle you came for. Worse, the pane's
    toggle sat under a table whose leftmost column was Streamlit's own
    selection checkbox -- two checkbox-shaped controls for one row, the
    inert-looking one being the real selector.

    Editing wins the trade. `on` is a real checkbox in the row, each
    numeric setting is a cell, and nothing is one click away that used to
    be. What genuinely cannot be a cell -- a check's word LISTS, and
    ste100's set-valued excluded_vocab_types -- moves below under a
    selector naming only the checks that have any, so the pane appears
    for the 9 rows it has content for instead of all 43."""
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
             "under one check, so \"is 'leverage' banned\" is a word "
             "search, not a row in this table.").strip().lower()
    shown = [r for r in rows
             if not needle or needle in r["check"].lower()
             or needle in r["catches"].lower() or needle in r["instead"].lower()]
    if not shown:
        st.caption("No check matches.")
        _word_matches(repo_root, full, needle)
        return

    numeric = _numeric_option_columns(rows)
    table, config = [], {
        "on": st.column_config.CheckboxColumn("on", width="small"),
        "check": st.column_config.TextColumn("check", width="medium", disabled=True),
        "what it catches": st.column_config.TextColumn(
            "what it catches", width="large", disabled=True),
    }
    # TextColumn, not NumberColumn, for a display reason that survived
    # two attempts at the numeric one: an empty cell in a NumberColumn
    # renders the literal "None" (object, float and pandas' nullable
    # Int64 all do it in 1.60), and these columns are SPARSE by design --
    # twelve of ste100's thirteen rows would read "None None" beside the
    # one row that has word limits. A text cell can be genuinely empty.
    # The value is still validated as an integer on the way back in.
    for name in numeric:
        config[name] = st.column_config.TextColumn(
            name.replace("_", " "), width="small",
            help=f"{name.replace('_', ' ')}, on the checks that have one. "
                 f"Blank means this check takes no such setting.")
    # Text, not a number: a check with no word list has no count, and an
    # empty NumberColumn cell renders the literal "None" -- which read as
    # a value on 9 of codewatch's 10 rows. Blank says "nothing here"
    # without saying it in a word.
    config["words"] = st.column_config.TextColumn(
        "words", width="small", disabled=True,
        help="Vocabulary this check matches against. Edit it below.")
    config["denies alone"] = st.column_config.TextColumn(
        "denies alone", width="small", disabled=True,
        help="This check denies a write by itself once it fires this many "
             "times, whatever the total flag count. Blank means it only "
             "counts toward the ruleset's shared threshold above.")
    config["last fired"] = st.column_config.TextColumn(
        "last fired", width="small", disabled=True,
        help="The newest gate event in this repo where this check flagged "
             "something. Blank means it has never fired here.")

    fired = _last_fired(repo_root, ruleset_id)
    for r in shown:
        counts = _list_counts(repo_root, r, full)
        entry = {"on": r["enabled"], "check": r["check"],
                 "what it catches": r["catches"],
                 "words": str(sum(counts.values())) if counts else "",
                 "denies alone": _blocks_alone_label(r),
                 "last fired": (relative_time(fired[r["check"]])
                                 if r["check"] in fired else "")}
        for name in numeric:
            info = r["options"].get(name)
            entry[name] = str(int(info["value"])) if info else ""
        table.append(entry)

    # Keyed per ruleset: switching Path swaps every row underneath, and a
    # shared key would carry the previous ruleset's edits onto whatever
    # rows happen to land in the same positions.
    edited = st.data_editor(
        table, width="stretch", hide_index=True, height=380, num_rows="fixed",
        key=f"checks_editor::{ruleset_id}", column_config=config,
        column_order=["on", "check", "what it catches", *numeric,
                      "words", "denies alone", "last fired"])
    _apply_check_edits(repo_root, module, shown, table, edited, numeric)
    _check_contents(repo_root, full, shown, ruleset_id)
    _word_matches(repo_root, full, needle)


def _blocks_alone_label(row):
    n = row["blocks_alone_at"]
    return "" if not n else ("⚠️ on sight" if n == 1 else f"⚠️ at {n}")


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


def check_edits(rows, before, after, numeric):
    """(toggles, options, error) for what actually changed in the table.

    Pure, and separate from the writing, because this is where the risk
    is: st.data_editor has no on_change reporting WHICH cell moved, so
    the only way to know is to diff the rendered rows against the
    returned ones (the shape _routing_table already uses), and a diff
    that is subtly wrong writes something nobody asked for. A pure
    function can be tested against the awkward cases -- a blank in a
    sparse column, a cleared value, typed nonsense -- without a browser
    and without touching the config file. See test_configure.py."""
    toggles, options = {}, {}
    for row, was, now in zip(rows, before, after):
        if bool(now.get("on")) != bool(was["on"]):
            toggles[row["check"]] = bool(now["on"])
        for name in numeric:
            fresh = str(now.get(name) or "").strip()
            # Blank on the LEFT means this check takes no such setting --
            # the column is sparse by design, so there is nothing to
            # write. Blank on the RIGHT means the value was cleared, and
            # this table has no meaning for "no threshold": the ruleset
            # declares one or it does not. Both are left alone.
            if not was[name] or not fresh or fresh == was[name]:
                continue
            try:
                options[name] = int(fresh)
            except ValueError:
                return {}, {}, f"{name} must be a whole number, not {fresh!r}"
    return toggles, options, None


def _apply_check_edits(repo_root, module, rows, before, after, numeric):
    """Write whatever check_edits found, and nothing else. Only genuine
    differences are written, so a rerun triggered by anything else on the
    page (a Path change, an undo) writes nothing."""
    toggles, options, error = check_edits(rows, before, after, numeric)
    if error:
        st.session_state["write_error"] = error
        return
    if not toggles and not options:
        return

    labels = ([f"{'enabled' if on else 'disabled'} {c}" for c, on in toggles.items()]
              + [f"set {module.RULESET_ID}.{n} to {v}" for n, v in options.items()])
    _snapshot(repo_root, "; ".join(labels))
    try:
        if toggles:
            module.set_checks_enabled(toggles)
        if options:
            module.set_options(options)
    except Exception as exc:
        st.session_state["write_error"] = str(exc)
        return
    st.rerun()


def _check_contents(repo_root, full, rows, ruleset_id):
    """The words and set-valued settings behind a check, for the checks
    that have any.

    Every row used to open a pane like this, and for 34 of the fleet's 43
    checks it held nothing but the on/off toggle -- which is now a cell in
    the row. So the selector lists only the checks with something actually
    inside, and says how many there are rather than presenting itself as
    the way to reach a check at all. With none, it does not render."""
    have = [r for r in rows if r["lists"]
            or any("choices" in i for i in r["options"].values())]
    if not have:
        return

    st.divider()
    if len(have) == 1:
        # A selectbox offering one choice is a control that does nothing.
        row = have[0]
        st.caption(f"Words and lists — `{row['check']}` is the only one "
                   f"of these checks with any.")
    else:
        labels = {r["check"]: f"{r['check']} — " + ", ".join(
            filter(None, [f"{len(r['lists'])} word list(s)" if r["lists"] else "",
                          "vocabulary types" if any("choices" in i for i in
                                                     r["options"].values()) else ""]))
            for r in have}
        picked = st.selectbox(
            f"Words and lists ({len(have)} of these {len(rows)} checks have any)",
            [r["check"] for r in have], key=f"check_contents::{ruleset_id}",
            format_func=lambda c: labels[c])
        row = next(r for r in have if r["check"] == picked)

    # One line, whole story: what the check catches, then the remedy --
    # the remedy used to float alone as "Instead: ..." with nothing on
    # screen saying instead of WHAT.
    st.caption(f"{row['catches']} — instead, {row['instead']}.")
    for name, info in row["options"].items():
        if "choices" in info:
            _option_control(repo_root, row, name, info)
    for list_id in row["lists"]:
        _term_list_block(repo_root, row, list_id, full)


def _option_control(repo_root, row, name, info):
    cols = st.columns([2, 6])
    key = f"opt::{row['ruleset']}::{name}"
    args = (repo_root, row["module"], name, key)
    # "choices" marks a closed-set option (e.g. ste100's
    # excluded_vocab_types) -- a multiselect over the ruleset's own
    # declared domain, not a number. Declared, not inferred from the
    # value's type: see rulesets/ste100/__init__.py's _OPTION_CHOICES.
    if "choices" in info:
        cols[0].multiselect(name.replace("_", " "), options=info["choices"],
                             default=info["value"],
                             key=key, on_change=_option_changed, args=args)
    else:
        cols[0].number_input(name.replace("_", " "), value=int(info["value"]),
                              step=1, key=key,
                              on_change=_option_changed, args=args)
    with cols[1]:
        st.caption("")
        # A list-valued default joins into plain words -- an f-string
        # would render its Python repr, brackets and quotes on screen.
        default = info["default"]
        if isinstance(default, list):
            default = ", ".join(default)
        st.caption(f"built-in default: {default}")


def _list_counts(repo_root, row, full):
    """{source: count} for every list this check owns, or {} for a check
    with no vocabulary behind it."""
    out = {}
    for list_id in row["lists"]:
        for source, n in _resolve_counts(repo_root, row["module"], list_id, full).items():
            out[source] = out.get(source, 0) + n
    return out


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
    st.markdown(f"**{spec.get('label') or list_id}** — "
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
        st.caption("This list takes no new words — it is published reference "
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

    "Is 'leverage' banned, and where" is a real question a check-keyed
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
        st.error(f"Would DENY — {len(blocking)} flag(s) need a person's judgment")
        for f in blocking:
            st.write(f"- **[{f['kind']}]** {f.get('label') or ''} — "
                     f"{f['detail'].get('note', '')}")
    elif result["mechanical_violations"]:
        st.warning(f"Would AUTO-FIX — {len(result['mechanical_violations'])} "
                   f"mechanical violation(s)")
        st.code(ruleset.apply_mechanical_fixes(text, file_path=full))
    else:
        st.success("Would PASS unchanged")
    non_blocking = [f for f in result["semantic_flags"] if f not in blocking]
    if non_blocking:
        with st.expander(f"{len(non_blocking)} non-blocking note(s)"):
            for f in non_blocking:
                st.write(f"- [{f['kind']}] {f.get('label') or ''}")
