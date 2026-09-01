#!/usr/bin/env python3
"""Runs both arms and scores them.

The gated arm reproduces what a real session does against the live hook:
write, get denied with a list of flags, rewrite, try again. It stops when
the text passes the ENFORCED checks or the iteration budget runs out.

Four arms, and three rules keep the result honest.

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


def split_checks(ruleset, enforced=None):
    """(enforced, held_out) check-id sets for `ruleset`."""
    every = set(ruleset.list_checks())
    enforced = set(enforced or DEFAULT_ENFORCED) & every
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


def run_arm_gated(generator, prompt, ruleset, enforced, max_iterations=4):
    messages = [{"role": "user", "content": prompt}]
    text = generator(messages)
    iterations = 1
    while iterations < max_iterations:
        flags = _blocking_enforced(ruleset, text, enforced)
        if not flags:
            return {"text": text, "iterations": iterations, "passed": True}
        messages = [{"role": "user", "content": prompt},
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
              on_progress):
    if on_progress:
        on_progress(prompt["id"])
    ungated = run_arm_ungated(generator, prompt["text"])
    control = run_arm_ungated(generator, prompt["text"])
    gated = run_arm_gated(generator, prompt["text"], ruleset, enforced,
                           max_iterations=max_iterations)
    # Matched compute: the same number of generations the gated arm spent
    # on THIS prompt, so the two differ only in whether the rewrite was
    # told what to fix.
    blind = run_arm_blind_revision(generator, prompt["text"],
                                    gated["iterations"])
    return {
        "id": prompt["id"],
        "prompt": prompt["text"],
        "ungated": {**ungated, "scores": score(ruleset, ungated["text"],
                                                enforced, held_out)},
        "control": {**control, "scores": score(ruleset, control["text"],
                                                enforced, held_out)},
        "gated": {**gated, "scores": score(ruleset, gated["text"],
                                            enforced, held_out)},
        "blind": {**blind, "scores": score(ruleset, blind["text"],
                                            enforced, held_out)},
    }


def run(prompts, ruleset, generator, enforced=None, max_iterations=4,
        on_progress=None, workers=1):
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
    args = (ruleset, generator, enforced, held_out, max_iterations, on_progress)
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
        "seconds": round(time.time() - started, 1),
        "rows": rows,
    }
