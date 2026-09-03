#!/usr/bin/env python3
"""Runs both arms and scores them.

The gated arm reproduces what a real session does against the live hook:
write, get denied with a list of flags, rewrite, try again. It stops when
the text passes the ENFORCED checks or the iteration budget runs out.

Five arms by default, and three rules keep the result honest.
`--compare` adds one per competing tool, `--combine` runs an instruction
inside the gated loop, and a prompt carrying follow-up turns makes every
arm multi-turn.

The fifth arm is INSTRUCTED: the enforced checks' rules stated in the
prompt itself, one generation, no gate. It is the free alternative --
a line in CLAUDE.md -- and the gate has to beat it to be worth
installing. See build_instruction.

The gated arm is never told about a held-out check. Not in the first
prompt, not in a revision. `_revision_message` is built only from
enforced flags, so held-out flags measure transfer rather than
instruction-following.

Every arm gets the same first prompt, so any difference between them
comes from the loop and nothing else.

A CONTROL arm runs, and it is what makes the numbers mean anything. It is
a second ungated generation from the identical prompt. Two independent
generations differ from each other for no reason but sampling, so the
control delta is this run's noise floor. A gate delta smaller than the
control delta is not a finding, whatever direction it points. The first
smoke run of this harness produced an eye-catching held-out difference on
a prompt where the gated loop never revised anything -- the arms were two
independent samples and nothing else -- which is exactly the mistake this
arm exists to make visible.
"""
import concurrent.futures
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evalab import metrics

# Enforced during the gated loop. Held-out is every other check in the
# ruleset, computed in split_checks so a ruleset gaining a check cannot
# silently leave it out of both sets.
#
# The split is by CONSTRUCTION, not at random: each side gets a mix of
# openers, hedging, punctuation habits and marketing register, so neither
# is a soft target. A run may override it, and a run that does should say
# so in its report.
# The structural half, added after the 30-prompt run showed the gate
# reaching zero on every lexical check while the document's SHAPE went
# untouched (5.99 structural flags per 1000 words before the gate, 6.12
# after). Enforcing these is the experiment that asks whether a gate
# pointed at shape can move what a gate pointed at wording could not.
STRUCTURAL_ENFORCED = frozenset({
    "bold_density",
    "thematic_break",
    "paragraph_uniformity",
    "title_case_heading",
    "rule_of_three",
    "participial_tail",
})

DEFAULT_ENFORCED = frozenset({
    "filler_opener",
    "colon_reveal",
    "vague_intensifier",
    "marketing_adjective",
    "weasel_attribution",
    "not_just_x_but_y",
    "emoji_in_prose",
    "id_label_lead",
    "canned_question_answer",
    "solicit_criticism",
    "entity_encoded_punctuation",
})


# RETRACTED, and left here as the retraction rather than deleted.
#
# A `calibrated` preset used to live at this spot, dropping four checks
# -- vague_intensifier, marketing_adjective, copula_avoidance,
# filler_verb -- on the grounds that they fired MORE on human prose than
# on generated prose across every control corpus measured.
#
# They do not. That verdict came from pairing a generated corpus with a
# human control that was mostly CPython docstrings, which carry no
# markdown at all. Re-measured against human MARKDOWN documentation and
# pre-2022 encyclopedia prose, the same four come out `no signal`,
# `disputed`, `disputed` and `disputed`. Not one is condemned:
#
#   copula_avoidance     no signal   (1.2x, 1.3x)
#   filler_verb          disputed    (discriminates on one, backwards on the other)
#   marketing_adjective  disputed    (silent on one, backwards on the other)
#   vague_intensifier    disputed    (discriminates on one, no signal on the other)
#
# That is the THIRD time in this project's evaluation history that a
# fairer corpus overturned a conclusion drawn from a narrower one --
# after the flattening effect that was an averaging artifact, and after
# colon_reveal, which read 1.0x against code documentation and 25.8x
# against encyclopedia prose. The pattern is worth more than any of the
# three findings: a verdict from one corpus shape is a hypothesis, and
# the unanimity rule in core.scan.consensus_verdicts only helps when the
# corpora actually differ in the dimension that matters.
#
# No preset replaces it. A check set nothing currently justifies cutting
# is not an oversight, and shipping a preset whose membership did not
# survive its own re-measurement would be worse than shipping none.


# ste100 shares no check id with slopwatch, so every slopwatch preset
# intersects it to NOTHING. That is why the ruleset doing the most work in
# this project's real gate history -- vocabulary, ing_form, modal, length
# and passive are the five most-fired checks across 77 live gate events --
# had never once been evaluated: the harness produced an empty enforced
# set, the gated arm never revised, and the run looked like a null result
# instead of a broken one.
#
# Split by construction like the others: a mix of sentence shape, verb
# form and punctuation on each side, so neither is a soft target.
STE100_ENFORCED = frozenset({
    "ing_form",
    "length",
    "passive",
    "punctuation",
    "trailing_condition",
    "perfect_tense",
})


# codewatch is the last ruleset with no evidence at all. slopwatch has nine
# runs and ste100 has one -- which found the gate indistinguishable from
# doing nothing there. codewatch gates every .py file in this repository,
# including the code this harness is written in, and has never been
# measured. Same split-by-construction rule: comment habits and code
# habits on both sides.
CODEWATCH_ENFORCED = frozenset({
    "narrative_comment",
    "print_debug",
    "generic_naming",
    "todo_stub",
})


PRESETS = {
    "lexical": lambda: DEFAULT_ENFORCED,
    "codewatch": lambda: CODEWATCH_ENFORCED,
    "ste100": lambda: STE100_ENFORCED,
    "structural": lambda: DEFAULT_ENFORCED | STRUCTURAL_ENFORCED,
}


class EmptyEnforcedSet(ValueError):
    """A preset that names none of this ruleset's checks."""


def split_checks(ruleset, enforced=None):
    """(enforced, held_out) check-id sets for `ruleset`.

    Raises when the intersection is empty. Returning an empty enforced
    set is worse than useless: the gated arm never revises, every arm
    becomes an independent sample of the same prompt, and the report says
    "the loop revised 0 of 30 prompts" -- which reads like a null result
    about the gate rather than a broken experiment. ste100 sat unmeasured
    behind exactly that silence.
    """
    name = enforced if isinstance(enforced, str) else None
    if isinstance(enforced, str):
        enforced = PRESETS[enforced]()
    every = set(ruleset.list_checks())
    enforced = set(enforced or DEFAULT_ENFORCED) & every
    if not enforced:
        raise EmptyEnforcedSet(
            f"preset {name or 'default'!r} names none of "
            f"{ruleset.RULESET_ID!r}'s checks, so the gated arm would never "
            f"revise and the run would measure nothing. This ruleset has: "
            f"{', '.join(sorted(every))}")
    return frozenset(enforced), frozenset(every - enforced)


def _flag_kinds(ruleset, text, only=None):
    result = ruleset.lint_and_gate(text)
    kinds = [f["kind"] for f in result["semantic_flags"]]
    if only is None:
        return kinds
    return [k for k in kinds if k in only]


def _revision_message(flags):
    lines = ["The text above has these problems. Rewrite it so none remain.",
             "Change nothing else, and keep the same length and purpose.", ""]
    for flag in flags:
        label = flag.get("label")
        detail = f" ({label})" if label else ""
        lines.append(f"- {flag['kind']}{detail}: {flag.get('instead') or ''}".rstrip())
    lines.append("")
    lines.append("Return only the rewritten text.")
    return "\n".join(lines)


def _blocking_enforced(ruleset, text, enforced):
    """Every enforced flag in this text. The loop treats all of them as
    blocking.

    This is deliberately STRICTER than any shipped default, and uniform
    across rulesets. An earlier version deferred to the ruleset's own
    blocking_semantic_flags and only fell back to "all enforced flags"
    when it denied nothing. That made the loop's strictness depend on
    whether some UNRELATED check happened to block: the same enforced
    flag drove a revision in one text and was ignored in another. The
    experiment asks what a blocking gate does to writing, so the arm has
    to block consistently, and the report says which policy ran.
    """
    flags = ruleset.lint_and_gate(text)["semantic_flags"]
    return [f for f in flags if f["kind"] in enforced]


def run_arm_ungated(generator, prompt):
    text = generator([{"role": "user", "content": prompt}])
    return {"text": text, "iterations": 1, "passed": None}


BLIND_REVISION = ("Rewrite the text above. Keep the same length and the "
                   "same purpose. Return only the rewritten text.")


def run_arm_blind_revision(generator, prompt, iterations):
    """The gated arm's compute, without the gate's information.

    Reads the same prompt and rewrites the same number of times the gated
    arm did for this prompt, told only to rewrite -- no flags, no check
    names, nothing about what to change.

    This arm exists because reading the 2026-09-01 texts side by side
    showed the gated runbook was plainly better than the ungated one, and
    it had also been generated twice. A second pass improves writing on
    its own. Without this control, a quality gain cannot be attributed to
    the flags rather than to the rewrite, and "the gate helped" would
    mean no more than "the model tried again".
    """
    messages = [{"role": "user", "content": prompt}]
    text = generator(messages)
    for _ in range(max(0, iterations - 1)):
        messages = [{"role": "user", "content": prompt},
                    {"role": "assistant", "content": text},
                    {"role": "user", "content": BLIND_REVISION}]
        text = generator(messages)
    return {"text": text, "iterations": iterations, "passed": None}


def run_arm_gated(generator, prompt, ruleset, enforced, max_iterations=4,
                   instruction=""):
    """The real write-lint-revise loop.

    `instruction`, when given, prefixes the FIRST prompt and every
    revision's restatement of it -- the combined arm. The leaderboard
    found a clean division of labour: a skill file generalises (10 to 12
    held-out flags) while the gate enforces (8 enforced flags), and
    every arm before this one was either/or. This asks whether they
    stack or compete for the same attention.
    """
    opening = instruction + prompt
    messages = [{"role": "user", "content": opening}]
    text = generator(messages)
    iterations = 1
    while iterations < max_iterations:
        flags = _blocking_enforced(ruleset, text, enforced)
        if not flags:
            return {"text": text, "iterations": iterations, "passed": True}
        messages = [{"role": "user", "content": opening},
                    {"role": "assistant", "content": text},
                    {"role": "user", "content": _revision_message(flags)}]
        text = generator(messages)
        iterations += 1
    passed = not _blocking_enforced(ruleset, text, enforced)
    return {"text": text, "iterations": iterations, "passed": passed}


def score(ruleset, text, enforced, held_out):
    """Every number for one piece of text."""
    row = dict(metrics.shape(text))
    kinds = _flag_kinds(ruleset, text)
    row["enforced_per_1k"] = round(metrics.flags_per_1k(kinds, text, only=enforced), 2)
    row["held_out_per_1k"] = round(metrics.flags_per_1k(kinds, text, only=held_out), 2)
    row["enforced_flags"] = sum(1 for k in kinds if k in enforced)
    row["held_out_flags"] = sum(1 for k in kinds if k in held_out)
    return row


def _run_one(prompt, ruleset, generator, enforced, held_out, max_iterations,
              on_progress, instructions, combined):
    if on_progress:
        on_progress(prompt["id"])
    turns = prompt.get("turns") or []
    if turns:
        # A prompt carrying follow-up turns makes EVERY arm multi-turn.
        # Mixing a one-shot arm with a five-turn one in the same row would
        # compare a first draft against a finished document and call the
        # difference an effect.
        def arm(instruction="", gated=False):
            return run_turns(generator, prompt["text"], turns,
                              ruleset=ruleset, enforced=enforced,
                              max_iterations=max_iterations,
                              instruction=instruction, gate=gated)

        ungated = arm()
        control = arm()
        arms = {name: arm(instruction=text)
                 for name, text in instructions.items()}
        gated = arm(gated=True)
        for name in combined:
            arms[f"{name}+gated"] = arm(instruction=instructions[name],
                                         gated=True)
    else:
        ungated = run_arm_ungated(generator, prompt["text"])
        control = run_arm_ungated(generator, prompt["text"])
        arms = {name: run_arm_instructed(generator, prompt["text"], text)
                 for name, text in instructions.items()}
        gated = run_arm_gated(generator, prompt["text"], ruleset, enforced,
                               max_iterations=max_iterations)
        for name in combined:
            arms[f"{name}+gated"] = run_arm_gated(
                generator, prompt["text"], ruleset, enforced,
                max_iterations=max_iterations, instruction=instructions[name])
    # Matched compute: the same number of generations the gated arm spent
    # on THIS prompt, so the two differ only in whether the rewrite was
    # told what to fix. In a multi-turn row the blind arm spends the same
    # total across the same turns, told only to rewrite at each one.
    if turns:
        # One blind revision PER TURN, not per turn plus one. An extra
        # turn gives this arm an extra pass at the document and an extra
        # column in the drift table, and both make it incomparable to
        # every other row.
        blind = run_turns(generator, prompt["text"],
                           [BLIND_REVISION] * len(turns),
                           ruleset=ruleset, enforced=enforced)
    else:
        blind = run_arm_blind_revision(generator, prompt["text"],
                                        gated["iterations"])
    return {
        "id": prompt["id"],
        "prompt": prompt["text"],
        "turns": turns,
        "ungated": {**ungated, "scores": score(ruleset, ungated["text"],
                                                enforced, held_out)},
        "control": {**control, "scores": score(ruleset, control["text"],
                                                enforced, held_out)},
        **{name: {**arm, "scores": score(ruleset, arm["text"],
                                          enforced, held_out)}
            for name, arm in arms.items()},
        "gated": {**gated, "scores": score(ruleset, gated["text"],
                                            enforced, held_out)},
        "blind": {**blind, "scores": score(ruleset, blind["text"],
                                            enforced, held_out)},
    }


def run(prompts, ruleset, generator, enforced=None, max_iterations=4,
        on_progress=None, workers=1, instructions=None, combined=None,
        complement=False):
    """Every arm over every prompt. Returns a result dict for report.py.

    `workers` parallelizes across PROMPTS, never within one. A prompt's
    own arms stay sequential and in order because the gated loop's next
    generation depends on the last one's flags, and because the blind arm
    has to spend whatever the gated arm spent -- neither is knowable in
    advance. Thirty prompts serially is about two hours of subprocess
    latency, almost all of it spent waiting.
    """
    enforced, held_out = split_checks(ruleset, enforced)
    started = time.time()
    instructions = dict(instructions or {})
    instructions.setdefault("instructed", build_instruction(ruleset, enforced))
    if "complement" in (instructions.get("_want") or ()) or complement:
        # The COMPLEMENT instruction: built from the checks the gate does
        # NOT enforce. The combined run showed why this matters. A block
        # generated from the enforced table restates what the gate is
        # about to enforce anyway, and barely stacks with it (23 tells
        # against 30, p = 0.17). stop-slop stacks properly (15, p = 0.017)
        # because it names things no check here enforces.
        #
        # Scoring note that must travel with any number from this arm:
        # for it, held-out flags are NO LONGER a transfer measurement.
        # They are instruction-following, because this arm was told about
        # them. Total tells is the only honest headline here, and it is
        # the one a reader cares about anyway.
        instructions["complement"] = build_instruction(ruleset, held_out)
    instructions.pop("_want", None)
    combined = [name for name in (combined or []) if name in instructions]
    args = (ruleset, generator, enforced, held_out, max_iterations, on_progress,
            instructions, combined)
    if workers > 1:
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(_run_one, p, *args) for p in prompts]
            done = [f.result() for f in futures]
        # Submission order, not completion order, so a saved result reads
        # the same however many workers produced it.
        rows = done
    else:
        rows = [_run_one(p, *args) for p in prompts]
    return {
        "ruleset": ruleset.RULESET_ID,
        "generator": generator.name,
        "generator_version": generator.version(),
        "enforced": sorted(enforced),
        "held_out": sorted(held_out),
        "max_iterations": max_iterations,
        "instruction": instructions["instructed"],
        "instructions": {name: text for name, text in instructions.items()},
        "intervention_arms": sorted(n for n in instructions if n != "instructed"),
        "combined_arms": [f"{n}+gated" for n in combined],
        "seconds": round(time.time() - started, 1),
        "rows": rows,
    }


# ---------------------------------------------------------------------------
# The instructed arm.
#
# Every arm above answers "does the gate beat trying again". None of them
# answers the cheaper question the operator asked and this harness kept
# routing around: does the gate beat simply TELLING the model the rules
# up front, the way a line in CLAUDE.md would?
#
# That alternative costs one generation, no hook, no install, no latency.
# If it captures most of what the gate captures, the gate is a
# complicated way to buy very little, and this project should say so.
#
# The instruction is built from the enforced checks' OWN metadata, not
# hand-written, for two reasons. It cannot be accidentally weakened
# relative to what the gate enforces, and a ruleset that gains a check
# gains it in both arms at once. This is deliberately the STRONGEST form
# of the alternative: the same information the gate would have delivered
# as a denial, delivered before the first word instead.

INSTRUCTION_HEADER = (
    "Follow these writing rules. They matter as much as the content:")
INSTRUCTION_FOOTER = (
    "Now write the following. Return only the requested text.")


def build_instruction(ruleset, enforced):
    """A CLAUDE.md-style preamble naming every enforced check's rule."""
    table = ruleset.list_checks()
    lines = [INSTRUCTION_HEADER, ""]
    for check_id in sorted(enforced):
        meta = table.get(check_id) or {}
        catches = (meta.get("catches") or "").strip()
        instead = (meta.get("instead") or "").strip()
        if catches and instead:
            lines.append(f"- {catches} -- {instead}")
        elif catches or instead:
            lines.append(f"- {catches or instead}")
        else:
            lines.append(f"- avoid whatever {check_id} names")
    lines += ["", INSTRUCTION_FOOTER, ""]
    return "\n".join(lines)


def run_arm_instructed(generator, prompt, instruction):
    """One generation, rules stated up front, no gate and no rewrite.

    Deliberately the cheapest arm in the run: it spends exactly what the
    ungated arm spends. If it lands near the gated arm, the gate's whole
    cost -- the extra generations, the hook, the install -- bought the
    difference between them and nothing more.
    """
    text = generator([{"role": "user", "content": instruction + prompt}])
    return {"text": text, "iterations": 1, "passed": None}


# ---------------------------------------------------------------------------
# Multi-turn.
#
# Every arm above generates once and then, at most, revises the same text.
# Real documents are written over many turns: draft, add a section, tighten
# the intro, rename the thing. This harness has been measuring first drafts
# and the tool it evaluates is used across whole sessions.
#
# Two things only a multi-turn run can see.
#
# DRIFT. Does a document get sloppier as it is edited? Nobody in this
# category has asked, and it is the question that would justify a gate most
# strongly -- or least.
#
# And the comparison this project has been publishing may be UNFAIR TO THE
# INSTRUCTION. In real use a CLAUDE.md line sits in context on every turn.
# The single-turn instructed arm gives it exactly one shot at one prompt.
# So the instruction is modelled here the way it actually works: present at
# every turn, not just the first.


def _gate_until_clean(generator, ruleset, enforced, messages, text,
                       max_iterations):
    """Revise `text` until the enforced checks pass or the budget runs out.

    Returns (text, generations_spent, passed). `max_iterations` counts the
    FIRST generation too, matching run_arm_gated, so a budget of 1 means
    no revision at all.
    """
    spent = 0
    while spent < max_iterations - 1:
        flags = _blocking_enforced(ruleset, text, enforced)
        if not flags:
            return text, spent, True
        text = generator(messages + [
            {"role": "assistant", "content": text},
            {"role": "user", "content": _revision_message(flags)}])
        spent += 1
    return text, spent, not _blocking_enforced(ruleset, text, enforced)


def run_turns(generator, prompt, turns, ruleset=None, enforced=None,
               max_iterations=1, instruction="", gate=False):
    """One arm across a document's whole life.

    `turns` are follow-up requests applied in order to the document the
    first prompt produced. When `ruleset` is given, the gate runs AFTER
    EVERY TURN with its own budget -- which is what the live hook does. It
    fires on each write, not once per document.

    `instruction`, when given, leads every turn rather than only the
    first. That is how a CLAUDE.md line actually behaves: it sits in
    context for the whole session. Giving it one shot at the opening
    prompt, which is what the single-turn arms do, understates it.

    Returns the usual arm dict plus `per_turn` -- the flag count after
    each turn, so drift is visible rather than only the endpoint.
    """
    # `ruleset` is always used for SCORING each turn -- drift is the point
    # of a multi-turn run and an unscored arm cannot show it. `gate` is a
    # separate decision: whether this arm also revises against the checks.
    gating = gate and ruleset is not None and max_iterations > 1
    history = [{"role": "user", "content": instruction + prompt}]
    text = generator(history)
    generations = 1
    passed = None
    if gating:
        text, spent, passed = _gate_until_clean(
            generator, ruleset, enforced, history, text, max_iterations)
        generations += spent
    per_turn = [_turn_score(ruleset, text, enforced)]

    for request in turns:
        history = history + [{"role": "assistant", "content": text},
                              {"role": "user", "content": instruction + request}]
        text = generator(history)
        generations += 1
        if gating:
            text, spent, passed = _gate_until_clean(
                generator, ruleset, enforced, history, text, max_iterations)
            generations += spent
        per_turn.append(_turn_score(ruleset, text, enforced))

    return {"text": text, "iterations": generations, "passed": passed,
             "per_turn": per_turn}


def _turn_score(ruleset, text, enforced):
    if ruleset is None:
        return None
    kinds = _flag_kinds(ruleset, text)
    return {"total": len(kinds),
             "enforced": sum(1 for k in kinds if k in enforced),
             "words": len(text.split())}
