#!/usr/bin/env python3
"""Turns a harness result into something a person can argue with.

The report leads with the held-out number, because that is the one the
gated arm could not aim at. It states the reading rules next to the
figures rather than in a doc nobody opens, so a result cannot be quoted
without the caveat that a six-prompt run settles nothing on its own.
"""
import statistics


def _mean(rows, arm, key):
    values = [r[arm]["scores"][key] for r in rows]
    return statistics.fmean(values) if values else 0.0


def _delta_line(label, ungated, gated, lower_is_better=True):
    delta = gated - ungated
    if abs(delta) < 1e-9:
        direction = "no change"
    else:
        better = (delta < 0) if lower_is_better else (delta > 0)
        direction = "better" if better else "WORSE"
    pct = ""
    if ungated:
        pct = f"  ({delta / ungated * 100:+.0f}%)"
    return (f"  {label:<26} {ungated:8.2f} -> {gated:8.2f}   "
            f"{delta:+7.2f}{pct}  {direction}")


def render(result):
    rows = result["rows"]
    out = []
    add = out.append

    add("stopslop A/B evaluation")
    add("=" * 66)
    add(f"ruleset          {result['ruleset']}")
    add(f"generator        {result['generator']} ({result['generator_version']})")
    add(f"prompts          {len(rows)}")
    add(f"max iterations   {result['max_iterations']}")
    add(f"wall clock       {result['seconds']}s")
    add("")
    add(f"enforced checks  {len(result['enforced'])}: "
        f"{', '.join(result['enforced'])}")
    add(f"held-out checks  {len(result['held_out'])}: "
        f"{', '.join(result['held_out'])}")
    add("")
    add("The gated arm was shown enforced flags only, never a held-out one.")
    add("Its loop treated EVERY enforced flag as blocking, which is stricter")
    add("than any shipped default -- the question is what a blocking gate")
    add("does to writing, so the arm has to block.")
    add("")

    revised = sum(1 for r in rows if r["gated"]["iterations"] > 1)
    add(f"THE GATED LOOP ACTUALLY REVISED {revised} OF {len(rows)} PROMPTS")
    add("-" * 66)
    if revised == 0:
        add("  Not one draft tripped an enforced check, so the gated arm is")
        add("  a third independent sample and this run measures nothing but")
        add("  generation variance. Every delta below is noise. Enforce")
        add("  checks the model actually trips, or use harder prompts.")
    else:
        add(f"  Only those {revised} carry any signal. On the rest the gated")
        add("  arm is a third independent sample of the same prompt.")
    add("")

    add("AVERAGES  (gate = ungated -> gated;  noise = ungated -> control)")
    add("-" * 66)
    for label, key, lower_better in [
            ("enforced flags /1k", "enforced_per_1k", True),
            ("HELD-OUT flags /1k", "held_out_per_1k", True),
            ("sentence length stdev", "sentence_length_stdev", False),
            ("type-token ratio", "type_token_ratio", False),
            ("words", "words", False)]:
        base = _mean(rows, "ungated", key)
        add(_delta_line(label, base, _mean(rows, "gated", key), lower_better))
        control = _mean(rows, "control", key)
        add(f"  {'  ^ noise floor':<26} {base:8.2f} -> {control:8.2f}   "
            f"{control - base:+7.2f}           (second ungated sample)")
        add("")

    iterations = statistics.fmean([r["gated"]["iterations"] for r in rows])
    passed = sum(1 for r in rows if r["gated"]["passed"])
    add(f"  gated arm: {iterations:.1f} generations per prompt on average, "
        f"{passed}/{len(rows)} reached a clean pass")
    add("")

    add("PER PROMPT (enforced /1k, held-out /1k, stdev)")
    add("-" * 66)
    add(f"  {'prompt':<20} {'enforced u->g':>16}  {'held-out u->g':>16}  "
        f"{'stdev u->g':>14}")
    for r in rows:
        u, g = r["ungated"]["scores"], r["gated"]["scores"]
        add(f"  {r['id']:<20} "
            f"{u['enforced_per_1k']:7.1f}->{g['enforced_per_1k']:<7.1f} "
            f"{u['held_out_per_1k']:7.1f}->{g['held_out_per_1k']:<7.1f} "
            f"{u['sentence_length_stdev']:6.1f}->{g['sentence_length_stdev']:<6.1f}")
    add("")

    add("HOW TO READ THIS")
    add("-" * 66)
    add("  Compare every gate delta against the noise floor printed under")
    add("  it. The control arm is a second ungated generation from the same")
    add("  prompt, so its delta is what this model varies by for no reason")
    add("  at all. A gate delta smaller than that is not a finding.")
    add("")
    add("  Enforced flags falling proves nothing on its own. The gated arm")
    add("  rewrote until they fell, so that number only confirms the loop")
    add("  ran.")
    add("")
    add("  The held-out number is the finding. It falls with the enforced")
    add("  one if the gate taught something general. It stays flat while")
    add("  enforced flags collapse if the gate taught avoidance of the")
    add("  specific patterns and nothing else.")
    add("")
    add("  Sentence-length stdev falling is the monotone warning: the model")
    add("  bought a clean score by flattening every sentence to one shape.")
    add("  No check rewards that number, so nothing can be tuned to it.")
    add("")
    add(f"  {len(rows)} prompts and one model settle nothing by themselves.")
    add("  Read the saved texts side by side before believing any of it.")
    return "\n".join(out)
