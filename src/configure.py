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

Packs stopped being a concept here. A pack is a source of words, words
belong to a list, a list belongs to a check -- so attaching one is a
control inside that check, acting on the rule the scope line names. Nothing
called "packs" needs its own place.

Two things are deliberately NOT folded. `by check / all words` keeps the
flat 2830-row vocabulary view, because "show me every word this path
knows" is a real question that a check-keyed layout cannot answer. And the
full routing table stays reachable behind the scope line, because rule
ORDER is load-bearing (first match wins) and order is invisible in a view
that only shows the winner.

Every edit applies immediately -- the same promise the page makes about
reaching the next gate call. Anything that cannot be inferred back from
the result (deleting a rule, renaming a glob, removing selected words)
confirms first, and the last write is always undoable, because every
mutation on this page lands in one file.
"""
import os

import streamlit as st

import rulesets
from core import config as core_config
from core import glossary_packs, terms as core_terms


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
                    if k.startswith(("chk::", "opt::", "scope_ruleset::"))]:
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
    probe, full, rule = _scope(repo_root)
    ruleset_id = rule["ruleset"] if rule else None
    _undo_bar()

    with st.container(border=True):
        _rules_section(repo_root, probe, full, ruleset_id)

    with st.container(border=True):
        _playground(repo_root, probe, full, ruleset_id)


def _scope(repo_root):
    """The path, the rule that governs it, and that rule made editable in
    place. Returns (probe, full path, rule dict or None).

    The scope line and the routing table were the same fact at two zoom
    levels: a sentence naming the winning rule, above a six-row grid that
    did not mark it. You read the sentence, then hunted the grid for your
    row. The winning rule is now edited where it is named; the grid is a
    disclosure, for adding and REORDERING (first match wins, so order is
    the one thing the folded view genuinely cannot express)."""
    cols = st.columns([2, 5])
    default = core_config.SYNTHETIC_TEXT_NAME
    probe = cols[0].text_input(
        "Configuring for path", value=default, key="scope_path",
        help="Any path in this repo. Routing decides the rest; the default "
             "is the synthetic name free text is treated as.").strip() or default
    full = os.path.join(repo_root, probe)
    rule = core_config.matching_rule(full, repo_root)

    ids = [m.RULESET_ID for m in rulesets.list_rulesets()]
    with cols[1]:
        if rule is None:
            st.caption("")
            st.markdown(f"`{probe}` → **no routing rule matches it**, so the "
                        f"gate never runs. Add a rule below.")
        else:
            inner = st.columns([3, 3])
            current = rule["ruleset"] or ""
            # The key is scoped to the GLOB, not to the widget's job. A
            # single "scope_ruleset" key carried its value across a change
            # of path, so the box showed the previous rule's ruleset while
            # naming the new rule -- and the write below fired on that
            # stale value. See _apply_on_change.
            key = f"scope_ruleset::{rule['glob']}"
            inner[0].selectbox(
                f"Gated by (rule `{rule['glob']}`)", [""] + ids,
                index=([""] + ids).index(current) if current in [""] + ids else 0,
                key=key, on_change=_route_changed,
                args=(repo_root, rule["glob"], key),
                help="Empty puts every file matching this glob out of scope.")
            with inner[1]:
                st.caption("")
                st.caption(f"{'out of scope' if not current else current} · "
                            f"{_pack_count(rule)} pack binding(s)")

    with st.expander(f"All routing rules — first match wins"):
        _routing_table(repo_root)
    return probe, full, rule


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


def _route_changed(repo_root, glob, key):
    chosen = st.session_state[key] or None
    _snapshot(repo_root, f"routed {glob} to {chosen or 'out of scope'}")
    rules = [{"glob": g, "ruleset": chosen if g == glob else r}
             for g, r, _ in core_config.rule_packs(repo_root)]
    try:
        core_config.save_rules(repo_root, rules, rulesets)
    except Exception as exc:
        st.session_state["write_error"] = str(exc)


def _check_toggled(repo_root, module, check_id, key):
    on = st.session_state[key]
    _snapshot(repo_root, f"{'enabled' if on else 'disabled'} {check_id}")
    try:
        module.set_checks_enabled({check_id: on})
    except Exception as exc:
        st.session_state["write_error"] = str(exc)


def _option_changed(repo_root, module, name, key):
    value = int(st.session_state[key])
    _snapshot(repo_root, f"set {module.RULESET_ID}.{name} to {value}")
    try:
        module.set_options({name: value})
    except Exception as exc:
        st.session_state["write_error"] = str(exc)


def _routing_table(repo_root):
    st.caption(f"`{os.path.basename(core_config.config_path(repo_root))}` — "
               "rules are tried top to bottom and the first match wins, so "
               "ORDER matters. Changes reach the next gate call with no restart.")
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
                      "inside the check whose words they feed -- they are "
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
    mode = st.segmented_control(
        "View", ["by check", "all words"], default="by check",
        key="rules_mode", label_visibility="collapsed")
    _deny_policy(ruleset_id)
    if mode == "all words":
        _all_words(repo_root, probe, full, ruleset_id)
    else:
        _by_check(repo_root, probe, full, ruleset_id)


def _deny_policy(ruleset_id):
    """What actually blocks a write. Text comes from the ruleset, formatted
    with its live option values, so the number in the sentence is the
    number in force."""
    if not ruleset_id:
        st.info("This path is out of scope, so nothing below runs on it.")
        return
    module = rulesets.get_ruleset(ruleset_id)
    policy = getattr(module, "DENY_POLICY", None)
    if not policy:
        return
    options = ({name: info["value"] for name, info in module.list_options().items()}
               if "options" in module.CAPABILITIES else {})
    try:
        text = policy["text"].format(**options)
    except KeyError as missing:
        text = policy["text"]        # a placeholder with no option behind it
        st.caption(f"(policy text names an unknown option {missing})")
    st.markdown(f"🚫 **{ruleset_id} denies a write:** {text}")


def _check_rows(ruleset_id):
    rows = []
    for module in rulesets.list_rulesets():
        if "checks" not in module.CAPABILITIES:
            continue
        options = ({n: i for n, i in module.list_options().items()}
                   if "options" in module.CAPABILITIES else {})
        always = set(getattr(module, "DENY_POLICY", {}).get("always_blocking", ()))
        owned = getattr(module, "CHECK_OPTIONS", {})
        lists = getattr(module, "TERM_LISTS", {})
        for check_id, meta in sorted(module.list_checks().items()):
            rows.append({
                "module": module, "check": check_id, "ruleset": module.RULESET_ID,
                "catches": meta["catches"], "instead": meta["instead"],
                "enabled": meta["enabled"], "blocks_alone": check_id in always,
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
    rows.sort(key=lambda r: (r["ruleset"] != ruleset_id, r["ruleset"], r["check"]))
    return rows


def _by_check(repo_root, probe, full, ruleset_id):
    """A dense grid, and the detail for one selected row beneath it.

    The first cut of this gave every check its own st.expander, following
    an ASCII sketch that drew a table with inline expansion. Streamlit
    cannot make that shape, and the approximation cost 6x the height for
    the same information: 44 bordered boxes, 2281px of widget chrome, a
    4114px page. It also lost column alignment, because each row collapsed
    into one markdown string, and it left the section rendered as a widget
    list beside two real grids, which is what made the page read as two
    unrelated idioms stitched together.

    Master/detail is the native answer to the gap Streamlit does have:
    st.dataframe supports row selection but is read-only, st.data_editor
    is editable but supports no selection, and a check row needs both a
    toggle and a detail affordance. Rather than fight that with a second
    control, the toggle moves into the detail -- reading this list is
    constant, and turning a check off is rare and worth seeing first."""
    rows = _check_rows(ruleset_id)
    here = [r for r in rows if r["ruleset"] == ruleset_id]
    off = sum(1 for r in rows if not r["enabled"])
    st.caption(f"{len(rows)} checks across every ruleset, {off} off. "
               f"**{len(here)}** run on `{probe}` and sort first. "
               f"Select a row for its tuning and its words.")

    cols = st.columns([3, 2])
    needle = cols[0].text_input("Search", key="rules_q").strip().lower()
    picked = cols[1].multiselect("Ruleset", sorted({r["ruleset"] for r in rows}),
                                  key="rules_rs")
    shown = [r for r in rows
             if (not needle or needle in r["check"].lower()
                 or needle in r["catches"].lower() or needle in r["instead"].lower())
             and (not picked or r["ruleset"] in picked)]
    if not shown:
        st.caption("Nothing matches.")
        return

    event = st.dataframe(
        [{"on": "✓" if r["enabled"] else "", "runs here": "✓" if r["ruleset"] == ruleset_id else "",
          "check": r["check"], "ruleset": r["ruleset"], "what it catches": r["catches"],
          "tuning": _tuning_summary(repo_root, r, full)} for r in shown],
        width="stretch", hide_index=True, height=380,
        on_select="rerun", selection_mode="single-row", key="checks_grid",
        column_config={
            "on": st.column_config.TextColumn("on", width="small"),
            "runs here": st.column_config.TextColumn("here", width="small"),
            "check": st.column_config.TextColumn("check", width="medium"),
            "ruleset": st.column_config.TextColumn("ruleset", width="small"),
            "what it catches": st.column_config.TextColumn("what it catches", width="large"),
            "tuning": st.column_config.TextColumn("tuning", width="medium"),
        })
    chosen = event.selection.rows
    if not chosen:
        st.caption("Nothing selected.")
        return
    _check_detail(repo_root, full, shown[chosen[0]], ruleset_id)


def _tuning_summary(repo_root, row, full):
    """The one-line answer to "is there anything inside this row" -- so the
    grid says which checks are worth opening without opening any."""
    bits = []
    if row["blocks_alone"]:
        bits.append("denies alone")
    for name, info in row["options"].items():
        bits.append(f"{name} {info['value']}")
    counts = _list_counts(repo_root, row, full)
    if counts:
        bits.append(f"{sum(counts.values())} words")
    return " · ".join(bits)


def _check_detail(repo_root, full, row, ruleset_id):
    live = row["ruleset"] == ruleset_id
    st.markdown(f"### `{row['check']}` · {row['ruleset']}")
    st.markdown(f"**Catches:** {row['catches']}  \n**Instead:** {row['instead']}")
    if not live:
        st.caption(f"Runs on files routed to {row['ruleset']}, not on this path.")

    key = f"chk::{row['ruleset']}::{row['check']}"
    st.toggle("Enabled", value=row["enabled"], key=key, on_change=_check_toggled,
               args=(repo_root, row["module"], row["check"], key))
    if row["blocks_alone"]:
        st.warning("This check denies a write on its own, whatever the flag "
                   "count. Turning it off changes what blocks.")
    for name, info in row["options"].items():
        _option_control(repo_root, row, name, info)
    for list_id in row["lists"]:
        _term_list_block(repo_root, row, list_id, full)


def _option_control(repo_root, row, name, info):
    cols = st.columns([2, 6])
    key = f"opt::{row['ruleset']}::{name}"
    cols[0].number_input(name, value=int(info["value"]), step=1, key=key,
                          on_change=_option_changed,
                          args=(repo_root, row["module"], name, key))
    with cols[1]:
        st.caption("")
        st.caption(f"shipped default {info['default']}")


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

    The sources summary, the detach control, the source filter and the
    suppressed list were four separate views of one idea, spread across a
    section. Here the summary IS the filter (click a source), the row IS
    the detach control, and a suppressed word is a word with a state
    rather than a collection of its own."""
    module = row["module"]
    spec = module.TERM_LISTS[list_id]
    layers = core_terms.resolve(spec, repo_root, module.RULESET_ID, list_id,
                                 file_path=full)
    packs = set(glossary_packs.AVAILABLE_PACKS)
    # Name the list. A check can own more than one -- ste100's `vocabulary`
    # stacks three, an allow list, a deny list and the project's own -- and
    # three unlabelled blocks of words read as one repeated widget.
    polarity = spec.get("polarity")
    st.markdown(f"**{spec.get('label') or list_id}** · `{list_id}` · "
                f"{len(layers['effective'])} words · "
                f"{'ALLOW' if polarity == 'allow' else 'DENY'} — "
                + ("words here stop being flagged." if polarity == "allow"
                   else "words here start being flagged."))

    counts = _resolve_counts(repo_root, module, list_id, full)
    key = f"{module.RULESET_ID}.{list_id}"
    active = st.session_state.get(f"srcfilter_{key}")
    for source, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
        cols = st.columns([3, 1, 2])
        selected = active == source
        if cols[0].button(f"{'▸ ' if selected else ''}{source}  ({n})",
                           key=f"src_{key}_{source}", width="stretch"):
            st.session_state[f"srcfilter_{key}"] = None if selected else source
            st.rerun()
        cols[1].caption("pack" if source in packs else
                         ("yours" if source == "yours" else "shipped"))
        if source in packs:
            with cols[2]:
                if st.button("Detach", key=f"det_{key}_{source}"):
                    _set_pack(repo_root, full, source, module.RULESET_ID, list_id,
                               attach=False)

    suppressed = core_terms.suppressed_terms(repo_root, module.RULESET_ID, list_id)
    if suppressed:
        cols = st.columns([3, 1, 2])
        selected = active == "suppressed"
        if cols[0].button(f"{'▸ ' if selected else ''}suppressed  ({len(suppressed)})",
                           key=f"src_{key}_suppressed", width="stretch"):
            st.session_state[f"srcfilter_{key}"] = None if selected else "suppressed"
            st.rerun()
        cols[1].caption("removed")

    _word_table(repo_root, module, list_id, layers, suppressed, active, key)
    _add_vocabulary(repo_root, module, list_id, full, spec, packs)


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
    shipped = [r for r in chosen if r["source"] != "yours"]
    detail = (f"{len(chosen)} word(s) go. "
              + (f"{len(shipped)} of them are shipped (a built-in or a pack "
                 f"word), so they are SUPPRESSED rather than deleted and stay "
                 f"restorable." if shipped else "All are your own, so they are deleted."))
    if _confirm(f"rm_{key}", f"Remove {len(chosen)} selected word(s)", detail):
        _snapshot(repo_root, f"removed {len(chosen)} word(s) from {list_id}")
        for r in chosen:
            try:
                module.remove_term(list_id, r["term"])
            except Exception as exc:
                st.error(f"{r['term']}: {exc}")
        st.rerun()


def _add_vocabulary(repo_root, module, list_id, full, spec, packs):
    """One control for both ways to add words.

    Adding a word and attaching a pack are the same verb at different
    scale, and they sat far apart on the page. This takes either: pick a
    pack from the list, or type a word that is not one."""
    attachable = sorted(packs) if spec.get("accepts_packs") else []
    cols = st.columns([3, 3, 1])
    entry = cols[0].selectbox(
        "Add a word, or pick a pack", [""] + attachable,
        accept_new_options=True, key=f"add_{module.RULESET_ID}_{list_id}",
        help=("Type a single word to register it here. Pick a pack to bind "
              "its whole vocabulary to this list, for files matching this "
              "path's routing rule.") if attachable else
             "Type a single word to register it here.")
    note = cols[1].text_input("Note", key=f"note_{module.RULESET_ID}_{list_id}",
                               placeholder="why this project uses it")
    with cols[2]:
        st.caption("")
        if st.button("Add", key=f"addbtn_{module.RULESET_ID}_{list_id}") and entry:
            if entry in packs:
                _set_pack(repo_root, full, entry, module.RULESET_ID, list_id,
                           attach=True)
            else:
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


def _set_pack(repo_root, full_path, pack, ruleset_id, list_id, attach):
    """Attach or detach on the rule that ACTUALLY gates this path -- the
    same first-match-wins call the gate makes."""
    rule = core_config.matching_rule(full_path, repo_root)
    if rule is None or rule["ruleset"] != ruleset_id:
        st.warning(f"This path is gated by {(rule or {}).get('ruleset') or 'nothing'}, "
                   f"not {ruleset_id}, so a pack attached here could never fire.")
        return
    current = list((rule.get("packs") or {}).get(list_id, []))
    new = current + [pack] if attach else [p for p in current if p != pack]
    _snapshot(repo_root, f"{'attached' if attach else 'detached'} {pack} "
                          f"on {rule['glob']}")
    try:
        core_config.set_rule_packs(repo_root, rule["glob"], list_id, new,
                                    known_packs=glossary_packs.AVAILABLE_PACKS)
        st.rerun()
    except Exception as exc:
        st.error(f"Not saved: {exc}")


# --- all words: the flat view a check-keyed layout cannot give ------------

def _all_words(repo_root, probe, full, ruleset_id):
    """Every word this path knows, in one table.

    Kept as a second VIEW rather than a second section. "Show me every word
    that reaches this file" is a real question, and a layout keyed on
    checks cannot answer it -- ste100's 2830 words sit under one check
    while codewatch's 12 sit under another."""
    rows = core_terms.term_index(rulesets, repo_root, file_path=full)
    for row in rows:
        row["list"] = f"{row['ruleset']}.{row['list']}"
    for row in core_terms.suppressed_index(rulesets, repo_root):
        rows.append({"term": row["term"], "ruleset": row["ruleset"],
                      "list": f"{row['ruleset']}.{row['list']}",
                      "source": "suppressed", "polarity": "", "note": ""})
    st.caption(f"**{len(rows)}** words reach `{probe}`, including any this "
               f"project suppressed. Every ruleset's lists are here.")

    cols = st.columns([3, 2, 2])
    needle = cols[0].text_input("Search", key="aw_q").strip().lower()
    lists = cols[1].multiselect("List", sorted({r["list"] for r in rows}), key="aw_list")
    sources = cols[2].multiselect("Source", sorted({r["source"] for r in rows}),
                                   key="aw_src")
    shown = [r for r in rows
             if (not needle or needle in r["term"].lower() or needle in r["note"].lower())
             and (not lists or r["list"] in lists)
             and (not sources or r["source"] in sources)]
    if len(shown) != len(rows):
        st.caption(f"{len(shown)} of {len(rows)} shown")
    if not shown:
        st.caption("Nothing matches.")
        return

    event = st.dataframe(
        [{k: r[k] for k in ("term", "list", "source", "note")} for r in shown],
        width="stretch", hide_index=True, height=420,
        on_select="rerun", selection_mode="multi-row", key="all_words")
    chosen = [shown[i] for i in event.selection.rows]
    if not chosen:
        st.caption("Select rows to remove them, or to restore a suppressed word.")
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
                            "A shipped word is suppressed rather than deleted, "
                            "and stays restorable."):
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
    """Text as if written to the scoped path -- the real gate call."""
    st.subheader("Try it")
    _override_prompt(repo_root)
    if not ruleset_id:
        st.caption(f"`{probe}` is out of scope, so the gate would not run.")
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
