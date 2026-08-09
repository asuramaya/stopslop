#!/usr/bin/env python3
"""The three config pages: Checks, Vocabulary, Routing.

One page per SUBJECT, not one page per config key and not one funnel
threaded through a path selector. The previous single Configure page
scoped everything -- checks, words, packs, the playground -- to one
probed path picked at the top, which welded four unrelated jobs into one
flow and made "tune codewatch's checks" start with "pick a glob". Each
page now stands alone:

- Checks: pick a ruleset, and every check is a row with its switch,
  threshold and action in the row (_by_check); the words and extra
  settings behind the few checks that have any sit below
  (_check_contents), and a Try-it playground linting with that ruleset.
- Vocabulary: one search across every word in every list -- "is
  `leverage` banned, and where" was always a search, never a view
  (_word_matches) -- and a browser for any single list, with add,
  remove, restore and the ste100 override flow.
- Routing: the editable first-match-wins rules table, which is the one
  place a PATH is genuinely the subject, and each rule's vocabulary
  pack bindings, which attach to a rule rather than a ruleset.

Every edit applies immediately, the same promise the pages make about
reaching the next gate call. Anything that cannot be read back off the
result (deleting a rule, renaming a glob, removing selected words)
confirms first, and the last write is always undoable, because every
mutation on these pages lands in one file (_snapshot / _undo_bar).

Two Streamlit constraints shaped more of this layout than taste did,
and each is documented where it bites: a grid cannot be editable AND
selectable (_routing_table), and a keyed widget outlives the data it
mirrors (the apply-on-change block below, and _undo_bar's key
clearing). The pages' own prose is gated by the same product it
configures -- see docs/embedded-prose.md.
"""
import os
import time

import streamlit as st

import rulesets
from core import config as core_config
from core import glossary_packs, history as core_history, terms as core_terms
from core import text as core_text


def relative_time(ts):
    """'2h ago' for a timestamp, '?' for a missing one. Lives here rather
    than dashboard.py because both need it and the import only runs one
    way (dashboard imports this module)."""
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


# "1 word" / "12 words" -- see core/text.py. Every count on these pages
# used to hand-roll its own "{n} word(s)", eighteen times over.
_n = core_text.n


# --- undo: one config file, so one mechanism covers every mutation --------

def _snapshot(project_root, label):
    """Remember the config file exactly as it is, under a human label.

    Deliberately a whole-file snapshot rather than a per-action inverse.
    Every control on these pages writes to stopslop.config.json through
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
                    if k.startswith(("param::", "pack::", "checks_editor::",
                                      "ruledisable::"))]:
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


# --- apply-on-change, done the one way that is safe -----------------------
#
# A keyed Streamlit widget returns SESSION STATE, not a fresh render of the
# data behind it. So the obvious shape for instant save --
#
#     value = st.selectbox(..., key="k")
#     if value != stored: write(value)
#
# -- is a silent-write bug, not a style choice. Whenever the stored value
# changes for any reason the widget did not cause (an undo, another process
# editing the config), the stale widget value differs from the new stored
# one and the write fires with nobody having touched anything. It cost this
# repo a real corruption: a scope box carried "slopwatch" across a path
# change and silently re-routed *.md away from ste100, in the config file,
# on page load. `on_change` fires only on genuine interaction, which is the
# whole difference. Callbacks also must not call st.rerun() -- Streamlit
# reruns after them anyway.


# --- Checks ---------------------------------------------------------------

def checks_page(repo_root):
    """Pick a ruleset; every check of it is a row with its own controls.

    The ruleset is the honest unit of selection here. A check belongs to
    a ruleset, full stop -- reaching one through a path selector forced a
    detour through routing (a separate concern with its own page) and
    broke the moment two globs routed to the same ruleset."""
    _undo_bar()
    ids = [m.RULESET_ID for m in rulesets.list_rulesets()
           if "checks" in m.CAPABILITIES]
    picked = st.segmented_control("Ruleset", ids, default=ids[0],
                                    key="checks_ruleset")
    ruleset_id = picked or ids[0]      # deselecting the pill means "no change"
    _routed_caption(repo_root, ruleset_id)
    _by_check(repo_root, ruleset_id)
    with st.expander("Try it: paste text, see what the gate does"):
        _playground(repo_root, ruleset_id)


def _routed_caption(repo_root, ruleset_id):
    """Routing context, read-only -- which files this ruleset's checks
    actually run on, and any check a RULE turns off on its own paths.
    Editing both facts lives on the Routing page; stating them here keeps
    "does this even apply, and why did it not fire there" answerable
    without a page switch. Without the second line, a check a rule
    disables shows as plain "on" in the table below, which is exactly the
    kind of true-but-incomplete display that reads as a lie the day the
    check fails to fire."""
    rules = [r for r in core_config.load_rules(repo_root)
             if ruleset_id in (r.get("ruleset"), r.get("embedded_prose"))]
    globs = [r["glob"] for r in rules if r.get("ruleset") == ruleset_id]
    if globs:
        st.caption("Runs on " + ", ".join(f"`{g}`" for g in globs)
                   + " (edit on Routing).")
    else:
        st.caption("Routed to no path in the current config -- add a rule "
                   "on Routing to use this ruleset.")
    embedded = [r["glob"] for r in rules if r.get("embedded_prose") == ruleset_id]
    if embedded:
        st.caption("Also runs on the prose EMBEDDED in "
                   + ", ".join(f"`{g}`" for g in embedded)
                   + " (strings, comments).")
    # A rule's disable list applies to every ruleset it invokes, so name
    # only the entries that are THIS ruleset's checks -- slopwatch's
    # colon_reveal disabled on *.py is noise on codewatch's page.
    own = set(rulesets.get_ruleset(ruleset_id).list_checks())
    exempt = [(r["glob"], [c for c in r["disable"] if c in own])
              for r in rules if r.get("disable")]
    exempt = [(g, checks) for g, checks in exempt if checks]
    if exempt:
        st.caption("Off per rule: "
                   + "; ".join(f"{', '.join(f'`{c}`' for c in checks)} on `{g}`"
                                for g, checks in exempt)
                   + " (edit on Routing).")


def _check_rows(ruleset_id):
    """Every check of the picked ruleset, one row each.

    One shape for every ruleset: each check carries its own {threshold,
    action}, plus any extra per-check numbers the ruleset declares
    (ste100's length carries its two word limits) under "params" --
    rendered in the check's own detail, never as a column shared across
    checks that don't have them."""
    module = rulesets.get_ruleset(ruleset_id)
    if "checks" not in module.CAPABILITIES:
        return module, []
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


def _by_check(repo_root, ruleset_id):
    """One editable table: every check, its on/off switch, and its own
    numbers, all in the row.

    This was master/detail -- a read-only grid, and a pane below carrying
    the toggle and any settings for whichever row you clicked. Streamlit
    forces that shape on anything needing both selection and editing (see
    _routing_table for the constraint), and the cost landed exactly where
    it hurt: most checks have NOTHING inside them but an on/off switch,
    so four rows in five made you click into a pane that was empty except
    for the toggle you came for.

    Editing wins the trade. `on` is a real checkbox in the row, threshold
    and action are cells, and nothing is one click away that used to be.
    What genuinely cannot be a cell -- a check's word LISTS, and its own
    extra params (length's word limits) -- moves below under a selector
    naming only the checks that have any (_check_contents)."""
    module, rows = _check_rows(ruleset_id)
    if not rows:
        st.caption(f"{ruleset_id} declares no checks.")
        return

    off = sum(1 for r in rows if not r["enabled"])
    needle = st.text_input(
        "Filter", key="rules_q", placeholder="a check name, or what it catches",
        label_visibility="collapsed",
        help="Filters this table. To search for a word across every "
             "list, use the Vocabulary page.").strip().lower()
    shown = [r for r in rows
             if not needle or needle in r["check"].lower()
             or needle in r["catches"].lower() or needle in r["instead"].lower()]
    st.caption(f"{len(rows)} checks" + (f", {off} turned off." if off else "."))
    if not shown:
        st.caption("No check matches.")
        return

    # threshold and action are real settings on EVERY row of every
    # ruleset, so a NumberColumn's blank-renders-as-"None" problem (the
    # reason older sparse columns used TextColumn) does not apply; there
    # is no blank cell left to render badly.
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

    # Keyed per ruleset: switching the pill swaps every row underneath,
    # and a shared key would carry the previous ruleset's edits onto
    # whatever rows happen to land in the same positions.
    edited = st.data_editor(
        table, width="stretch", hide_index=True, height=380, num_rows="fixed",
        key=f"checks_editor::{ruleset_id}", column_config=config,
        column_order=["on", "check", "what it catches",
                      "threshold", "action", "last fired"])
    _apply_check_edits(repo_root, module, shown, table, edited)
    _check_contents(repo_root, shown, ruleset_id)


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
    """(toggles, check_config_changes, error) for the checks table.

    The table writes what this function says changed, so a false positive
    here is a config write nobody asked for, and a false negative is an
    edit that silently does not save. st.data_editor has no on_change
    reporting WHICH cell moved -- it returns the whole table -- so the
    diff IS the change detection, and it runs on EVERY rerun, including
    reruns nothing to do with this table (a pill change, an Undo). "No
    edit" therefore has to be the reliable case, not the lucky one. Pure,
    and separate from the writing, so the awkward cases are testable
    without a browser -- see test_configure.py. `check_config_changes` is
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
    else on the page (a pill change, an undo) writes nothing."""
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


def _check_contents(repo_root, rows, ruleset_id):
    """The extra settings behind a check, for the checks that have any --
    and a POINTER, never an editor, for a check's word lists.

    Words used to be curated right here too, which put the whole
    word-table/add/override machinery on two pages at once (this one and
    Vocabulary) with separate widget state each. One home per act now:
    tuning a check's behaviour happens here; changing what words feed it
    happens on Vocabulary, and this pane says so with the list's name
    and live count rather than duplicating the controls."""
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
            filter(None, [_n(len(r['lists']), "word list") if r["lists"] else "",
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
    module = row["module"]
    for list_id in row["lists"]:
        spec = module.TERM_LISTS[list_id]
        layers = core_terms.resolve(spec, repo_root, module.RULESET_ID, list_id)
        polarity = spec.get("polarity")
        st.caption(f"**{spec.get('label') or list_id}**: "
                   f"{_n(len(layers['effective']), 'word')}; "
                   + ("a word here stops being flagged. "
                      if polarity == "allow" else "a word here gets flagged. ")
                   + "Curate it on Vocabulary.")


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


def _playground(repo_root, ruleset_id):
    """Text linted with the picked ruleset -- the real gate call.

    Lints as a file routed to this ruleset would be linted: the synthetic
    path from its first routing rule carries that rule's vocabulary packs
    into the call. With no rule routing to it, the ruleset's built-ins
    alone apply."""
    stored = core_config.rule_packs(repo_root)
    glob = next((g for g, r, _p in stored if r == ruleset_id), None)
    full = (os.path.join(repo_root, _synthetic_path_for_glob(glob))
            if glob else None)
    st.caption(f"Linted with `{ruleset_id}`, exactly as the gate would"
               + (f" -- with the vocabulary the `{glob}` rule carries."
                  if glob else "."))
    text = st.text_area("Text", height=120, key="playground_text",
                         placeholder="Paste a sentence or a snippet...")
    if not (st.button("Lint it", type="primary", key="lint_btn") and text.strip()):
        return

    ruleset = rulesets.get_ruleset(ruleset_id)
    result = ruleset.lint_and_gate(text, file_path=full)
    blocking = ruleset.blocking_semantic_flags(result["semantic_flags"])
    if blocking:
        verb = "needs" if len(blocking) == 1 else "need"
        st.error(f"Would DENY: {_n(len(blocking), 'flag')} {verb} a person's judgment")
        # Same per-flag format the hook's own deny message uses -- and no
        # bolded [tag] opening each item, which is slopwatch's own
        # bold_bullet_lead pattern, caught here by the dogfooding pass.
        for f in blocking:
            note = f['detail'].get('note', '')
            st.write(f"- [{f['kind']}] {f.get('label') or ''}"
                     + (f": {note}" if note else ""))
    elif result["mechanical_violations"]:
        st.warning(f"Would AUTO-FIX: "
                   + _n(len(result['mechanical_violations']), "mechanical violation"))
        st.code(ruleset.apply_mechanical_fixes(text, file_path=full))
    else:
        st.success("Would PASS unchanged")
    non_blocking = [f for f in result["semantic_flags"] if f not in blocking]
    if non_blocking:
        with st.expander(_n(len(non_blocking), "non-blocking note")):
            for f in non_blocking:
                st.write(f"- [{f['kind']}] {f.get('label') or ''}")


# --- Vocabulary -----------------------------------------------------------

def vocabulary_page(repo_root):
    """Every word in every list, searchable; any single list, browsable.

    "Is `leverage` banned, and where" is a real question a check-keyed
    table cannot answer -- ste100's 2830 words sit under ONE check while
    codewatch's 12 sit under another. Search is the primary verb here;
    the list browser below it covers curation (add, remove, restore) for
    one list at a time."""
    _undo_bar()
    needle = st.text_input(
        "Search every word", key="vocab_q",
        placeholder="a word, e.g. leverage",
        help="Reaches every word in every ruleset's lists, plus every "
             "suppressed word.").strip().lower()
    if needle:
        if not _word_matches(repo_root, needle):
            st.caption("No word in any list matches.")
        return

    entries = [(m, lid, spec)
               for m in rulesets.list_rulesets()
               for lid, spec in sorted(getattr(m, "TERM_LISTS", {}).items())]
    if not entries:
        st.caption("No ruleset declares a term list.")
        return
    labels = [f"{m.RULESET_ID} · {spec.get('label') or lid}"
              for m, lid, spec in entries]
    idx = st.selectbox("List", range(len(entries)), key="vocab_list",
                        format_func=lambda i: labels[i])
    module, list_id, _spec = entries[idx]
    _term_list_block(repo_root, module, list_id)


def _word_matches(repo_root, needle):
    """Words matching the search, across every ruleset's lists. Returns
    whether anything matched. Selection keeps the remove/restore
    operations; the CLI's terms listing remains the way to dump
    everything."""
    rows = core_terms.term_index(rulesets, repo_root)
    for row in rows:
        row["list"] = f"{row['ruleset']}.{row['list']}"
    for row in core_terms.suppressed_index(rulesets, repo_root):
        rows.append({"term": row["term"], "ruleset": row["ruleset"],
                      "list": f"{row['ruleset']}.{row['list']}",
                      "source": "suppressed", "polarity": "", "note": ""})
    hits = [r for r in rows
            if needle in r["term"].lower() or needle in r["note"].lower()]
    if not hits:
        return False

    st.caption(f"{_n(len(hits), 'matching word')}, in every ruleset's lists "
               f"project-wide -- the list column says which gate each one "
               f"belongs to.")
    event = st.dataframe(
        [{k: r[k] for k in ("term", "list", "source", "note")} for r in hits],
        width="stretch", hide_index=True, height=min(420, 40 + 35 * len(hits)),
        on_select="rerun", selection_mode="multi-row", key="word_matches")
    chosen = [hits[i] for i in event.selection.rows]
    if not chosen:
        return True

    restore = [r for r in chosen if r["source"] == "suppressed"]
    remove = [r for r in chosen if r["source"] != "suppressed"]
    if restore and st.button(f"Restore {len(restore)}", key="aw_restore"):
        _snapshot(repo_root, f"restored {_n(len(restore), 'word')}")
        for r in restore:
            rulesets.get_ruleset(r["ruleset"]).add_term(r["list"].split(".", 1)[1],
                                                         r["term"])
        st.rerun()
    if remove and _confirm("aw_rm", f"Remove {_n(len(remove), 'selected word')}",
                            "A built-in or pack word is suppressed rather than "
                            "deleted, and stays restorable."):
        _snapshot(repo_root, f"removed {_n(len(remove), 'word')}")
        for r in remove:
            try:
                rulesets.get_ruleset(r["ruleset"]).remove_term(
                    r["list"].split(".", 1)[1], r["term"])
            except Exception as exc:
                st.error(f"{r['term']}: {exc}")
        st.rerun()
    return True


def _resolve_counts(repo_root, module, list_id):
    layers = core_terms.resolve(module.TERM_LISTS[list_id], repo_root,
                                 module.RULESET_ID, list_id)
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


def _term_list_block(repo_root, module, list_id):
    """A list's words: where they come from, what they are, how to add.

    The sources summary, the source filter and the suppressed list were
    three separate views of one idea, spread across a section. Here the
    summary IS the filter (click a source), and a suppressed word is a
    word with a state rather than a collection of its own. Attaching or
    detaching a whole PACK is not here -- packs bind to a routing rule,
    so that control lives on the Routing page; a source labelled "pack"
    below is still informational, naming where a word came from."""
    spec = module.TERM_LISTS[list_id]
    layers = core_terms.resolve(spec, repo_root, module.RULESET_ID, list_id)
    packs = set(glossary_packs.AVAILABLE_PACKS)
    # Name the list. A check can own more than one -- ste100's `vocabulary`
    # stacks three, an allow list, a deny list and the project's own -- and
    # three unlabelled blocks of words read as one repeated widget. One
    # statement of each fact: the label (the id lives in its tooltip, for
    # cross-reference with the packs control), the count, and what being
    # on the list DOES, in plain words.
    polarity = spec.get("polarity")
    st.markdown(f"**{spec.get('label') or list_id}**: "
                f"{_n(len(layers['effective']), 'word')}; "
                + ("a word here stops being flagged." if polarity == "allow"
                   else "a word here gets flagged."),
                help=f"list id: `{list_id}`")
    _pack_feed_caption(repo_root, module, list_id)

    counts = _resolve_counts(repo_root, module, list_id)
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
    # right under the Add control that caused it. Guarded to this list so
    # a check with several lists shows the prompt once, under the right
    # one.
    pending = st.session_state.get("refused")
    if (pending and pending["list"] == list_id
            and pending["ruleset"] == module.RULESET_ID):
        _override_prompt(repo_root)


def _pack_feed_caption(repo_root, module, list_id):
    """Where this list gets pack vocabulary from, if anywhere -- read-only
    here, because a pack binds to a ROUTING RULE, not to the list: two
    rules routed to the same ruleset can feed it different packs. The
    words above are the list's own layers; pack words apply on the paths
    whose rule carries them."""
    bound = [(g, p.get(list_id)) for g, r, p in core_config.rule_packs(repo_root)
             if r == module.RULESET_ID and p and p.get(list_id)]
    if bound:
        st.caption("Packs feed this list per routing rule: "
                   + "; ".join(f"`{g}` ← {', '.join(pack_ids)}"
                                for g, pack_ids in bound)
                   + ". Attach or detach packs on Routing.")


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
            _snapshot(repo_root, f"restored {_n(len(chosen), 'word')} to {list_id}")
            for r in chosen:
                module.add_term(list_id, r["term"])
            st.rerun()
        return
    not_yours = [r for r in chosen if r["source"] != "yours"]
    verb = "goes" if len(chosen) == 1 else "go"
    not_yours_verb = "comes" if len(not_yours) == 1 else "come"
    detail = (f"{_n(len(chosen), 'word')} {verb}. "
              + (f"{len(not_yours)} of them {not_yours_verb} from a built-in list or a "
                 f"pack, so they are suppressed rather than deleted and stay "
                 f"restorable." if not_yours else "All are your own, so they are deleted."))
    if _confirm(f"rm_{key}", f"Remove {_n(len(chosen), 'selected word')}", detail):
        _snapshot(repo_root, f"removed {_n(len(chosen), 'word')} from {list_id}")
        for r in chosen:
            try:
                module.remove_term(list_id, r["term"])
            except Exception as exc:
                st.error(f"{r['term']}: {exc}")
        st.rerun()


def _add_vocabulary(repo_root, module, list_id, spec):
    """Add a single word to a term list."""
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


# --- Routing --------------------------------------------------------------

def routing_page(repo_root):
    """Which files go to which ruleset, and everything else a rule
    carries: its vocabulary packs, its embedded-prose ruleset, and the
    checks it turns off on its own paths.

    The one page where a PATH is genuinely the subject. Rule ORDER is
    load-bearing (first match wins) and invisible in any view that only
    shows a winner, so the whole table is the control -- editable in
    place, always fully visible. The probe box below it answers the
    question the order exists to settle: which single rule decides a
    given file."""
    _undo_bar()
    st.caption("First match wins; order matters. An empty ruleset cell "
               "means out of scope entirely (like `.claude/*`).")
    _routing_table(repo_root)
    _path_probe(repo_root)

    scoped = [r for r in core_config.load_rules(repo_root) if r.get("ruleset")]
    if not scoped:
        return
    st.divider()
    labels = [f"{r['glob']} → {r['ruleset']}" for r in scoped]
    idx = st.selectbox("Rule", range(len(scoped)), key="routing_focus",
                        format_func=lambda i: labels[i],
                        help="Everything below binds to this one rule, not "
                             "to its ruleset: two rules routed to the same "
                             "ruleset can carry different packs and "
                             "different exemptions.")
    rule = scoped[idx]
    if rule.get("embedded_prose"):
        st.caption(f"Also runs `{rule['embedded_prose']}` on the prose "
                   f"embedded in these files (strings, comments).")
    _rule_packs_editor(repo_root, rule)
    _rule_disable_editor(repo_root, rule)


def _path_probe(repo_root):
    """Type a path, get the one rule that decides it -- the gate's own
    resolver, not a lookalike. "What happens to this file" is the
    question first-match-wins exists to settle, and the table alone
    makes the reader run the match in their head."""
    probe = st.text_input(
        "Test a path", key="route_probe",
        placeholder="which rule wins for e.g. docs/notes.md?").strip()
    if not probe:
        return
    rule = core_config.matching_rule(os.path.join(repo_root, probe), repo_root)
    if rule is None:
        st.caption(f"`{probe}`: no rule matches -- the gate never runs on it.")
        return
    if rule.get("ruleset") is None:
        st.caption(f"`{probe}`: rule `{rule['glob']}` puts it out of scope. "
                   f"Nothing is checked.")
        return
    parts = [f"`{probe}`: rule `{rule['glob']}` wins → `{rule['ruleset']}`"]
    if rule.get("embedded_prose"):
        parts.append(f"embedded prose → `{rule['embedded_prose']}`")
    if rule.get("disable"):
        parts.append("off here: " + ", ".join(f"`{c}`" for c in rule["disable"]))
    n_packs = _pack_count(rule)
    if n_packs:
        parts.append(_n(n_packs, "pack binding"))
    st.caption("; ".join(parts) + ".")


def _rule_disable_editor(repo_root, rule):
    """Which checks this rule turns off on its own paths -- the per-path
    exemption disabled_checks_for_path unions into every gate call, which
    used to exist only as hand-written JSON. One direction only: a rule
    can turn a check off for its paths, never back on past a project-wide
    disable (see core.config.disabled_checks_for_path).

    Offers the checks of every ruleset the rule invokes -- the host and
    the embedded-prose ruleset -- because the disable list applies to
    both."""
    known = {}
    for ruleset_id in {rule.get("ruleset"), rule.get("embedded_prose")} - {None}:
        module = rulesets.get_ruleset(ruleset_id)
        if "checks" in module.CAPABILITIES:
            for check_id in module.list_checks():
                known[check_id] = ruleset_id
    if not known:
        return
    current = [c for c in (rule.get("disable") or []) if c in known]
    key = f"ruledisable::{rule['glob']}"
    st.multiselect(
        f"Checks turned off on `{rule['glob']}`", sorted(known),
        default=current, key=key,
        format_func=lambda c: f"{c} ({known[c]})",
        placeholder="No per-rule exemptions",
        on_change=_rule_disable_changed,
        args=(repo_root, rule["glob"], sorted(known), key),
        help="These checks do not run on this rule's paths. Everywhere "
             "else they keep their setting from the Checks page.")


def _rule_disable_changed(repo_root, glob, known, key):
    chosen = st.session_state[key]
    _snapshot(repo_root, f"set per-rule exemptions on {glob} to "
                          f"{', '.join(chosen) or '(none)'}")
    try:
        core_config.set_rule_disable(repo_root, glob, chosen, known_checks=known)
    except Exception as exc:
        st.session_state["write_error"] = str(exc)


def _routing_table(repo_root):
    """The editable first-match-wins rules table.

    A first cut of this drew a SECOND table just to make a row clickable:
    st.dataframe selects but can't edit, st.data_editor edits but can't
    select, so "pick a rule" and "edit a rule" got two separate grids,
    one of them inert. The rule selectbox below does the picking for the
    packs editor -- one line, not a second copy of the table."""
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
                   ", ".join(f"{_n(n, 'pack binding')} on `{g}`" for g, n in lost.items()) +
                   ". Re-attach them on the rule that replaces each one.")
    if _confirm("routing_del", f"Apply routing change ({_n(len(gone), 'rule')} removed)",
                 detail):
        _snapshot(repo_root, f"removed {_n(len(gone), 'routing rule')}")
        try:
            core_config.save_rules(repo_root, incoming, rulesets)
            st.rerun()
        except Exception as exc:
            st.error(f"Not saved: {exc}")


def _rule_packs_editor(repo_root, rule):
    """Which vocabulary packs feed the focused rule's term lists.

    Select the list first, only if the ruleset has more than one that
    takes packs -- most rulesets do (ste100's project_terms, codewatch's
    generic_naming, all five of slopwatch's deny lists), which is exactly
    why this reads TERM_LISTS rather than naming a list: a control that
    only knew about ste100's one would already be wrong for the other
    two. The label names the focused glob so the control cannot be
    misread as ruleset-wide -- packs bind to one rule."""
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
    # check) -- the Checks page is searchable by check id, not list id,
    # and the two only happen to match for rulesets with 1:1 lists.
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


def _pack_count(rule):
    return sum(len(v) for v in (rule.get("packs") or {}).values())


def _synthetic_path_for_glob(glob):
    """A literal path fnmatch would actually match against `glob` -- for
    "Try it" and any pack/context resolution downstream, which need a
    concrete path, not a pattern. Every wildcard segment becomes a fixed
    stand-in; a literal glob (no "*") is already a real path and passes
    through untouched. The same role core.config.SYNTHETIC_TEXT_NAME
    plays for free text with no file at all, generalized to any glob
    instead of hardcoding "*.md"."""
    return glob.replace("*", "__probe__") if "*" in glob else glob
