#!/usr/bin/env python3
"""Turns a harness result into something a person can argue with.

The report leads with the held-out number, because that is the one the
gated arm could not aim at. It states the reading rules next to the
figures rather than in a doc nobody opens, so a result cannot be quoted
without the caveat that a six-prompt run settles nothing on its own.
"""
import statistics


def _arms(rows):
    """Arms present in this result, in reading order.

    `blind` and `instructed` are absent from runs recorded before those
    arms existed, so a saved result from an earlier run still renders.
    Competing interventions are named at runtime, so anything present on
    a row that is not a known arm and carries scores is one of those, and
    it is listed after `instructed` in a stable alphabetical order.
    """
    order = ("ungated", "control", "blind", "instructed")
    if not rows:
        return []
    known = set(order) | {"gated"}
    extra = sorted(k for k, v in rows[0].items()
                    if k not in known and isinstance(v, dict) and "scores" in v)
    return [a for a in order if a in rows[0]] + extra + (
        ["gated"] if "gated" in rows[0] else [])


def _revised(rows):
    """Prompts where the gated loop actually rewrote something.

    Everywhere else the gated arm generated once and stopped, which makes
    it a third independent sample of the same prompt and nothing more.
    Averaging those in does not merely dilute an effect, it can invent
    one: run 2 showed an 11% drop in sentence-length variance across all
    eight prompts that vanished when restricted to the four the gate
    touched. The apparent flattening was sampling noise from prompts the
    gate never acted on.
    """
    return [r for r in rows if r["gated"]["iterations"] > 1]


def _total(rows, arm, key):
    return sum(r[arm]["scores"][key] for r in rows)


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
    if result.get("prompt_set"):
        note = ("real content, a fair base rate"
                 if result["prompt_set"] == "technical"
                 else "CHOSEN to produce flags -- not a base rate")
        add(f"prompt set       {result['prompt_set']} ({note})")
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

    signal = _revised(rows)
    add("TOTAL FLAGS  (a percentage hides how few these are)")
    add("-" * 66)
    add(f"  {'arm':<10} {'words':>7} {'enforced':>10} {'held-out':>10}"
        f"   {'| revised-only: enf':>20} {'held':>5}")
    for arm in _arms(rows):
        tail = ""
        if signal:
            tail = (f"   |{_total(signal, arm, 'enforced_flags'):19} "
                     f"{_total(signal, arm, 'held_out_flags'):5}")
        add(f"  {arm:<10} {_total(rows, arm, 'words'):7} "
            f"{_total(rows, arm, 'enforced_flags'):10} "
            f"{_total(rows, arm, 'held_out_flags'):10}{tail}")
    add("")
    add("  Read these before any percentage below. A 41% held-out drop in")
    add("  the 2026-09-01 run was two flags becoming one.")
    add("")

    competitors = result.get("intervention_arms") or []
    if competitors:
        add("LEADERBOARD  (total tells, fewer is better; generations spent)")
        add("-" * 66)
        base = _total(rows, "ungated", "enforced_flags") + \
            _total(rows, "ungated", "held_out_flags")
        board = []
        for arm in _arms(rows):
            total = _total(rows, arm, "enforced_flags") + \
                _total(rows, arm, "held_out_flags")
            gens = statistics.fmean([r[arm]["iterations"] for r in rows])
            cut = f"{(total - base) / base * 100:+.0f}%" if base else "--"
            board.append((total, arm, gens, cut))
        for total, arm, gens, cut in sorted(board):
            add(f"  {arm:<22} {total:6}  {cut:>6}   {gens:.2f} generations")
        add("")
        add("  Every arm above ran the same prompts in the same run. The")
        add("  competing skill files are vendored under src/evalab/")
        add("  interventions/ with their licenses; each is used in full,")
        add("  references included, which is the strongest form of it.")
        add("")

    scope = signal if signal else rows
    scope_label = (f"the {len(signal)} prompts the loop revised"
                    if signal else "ALL prompts (the loop revised none)")
    add(f"AVERAGES over {scope_label}")
    add("  (gate = ungated -> gated;  noise = ungated -> control)")
    add("-" * 66)
    for label, key, lower_better in [
            ("enforced flags /1k", "enforced_per_1k", True),
            ("HELD-OUT flags /1k", "held_out_per_1k", True),
            ("sentence length stdev", "sentence_length_stdev", False),
            ("type-token ratio", "type_token_ratio", False),
            ("words", "words", False)]:
        base = _mean(scope, "ungated", key)
        add(_delta_line(label, base, _mean(scope, "gated", key), lower_better))
        control = _mean(scope, "control", key)
        add(f"  {'  ^ noise floor':<26} {base:8.2f} -> {control:8.2f}   "
            f"{control - base:+7.2f}           (second ungated sample)")
        if scope and "blind" in scope[0]:
            blind = _mean(scope, "blind", key)
            add(f"  {'  ^ rewrite alone':<26} {base:8.2f} -> {blind:8.2f}   "
                f"{blind - base:+7.2f}           (same compute, no flags)")
        if scope and "instructed" in scope[0]:
            told = _mean(scope, "instructed", key)
            add(f"  {'  ^ TOLD THE RULES':<26} {base:8.2f} -> {told:8.2f}   "
                f"{told - base:+7.2f}           (ONE generation, no gate)")
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
    add("  These averages cover only the prompts the gate actually acted")
    add("  on. Including the rest does not just dilute an effect, it can")
    add("  invent one: this report's own earlier shape averaged in prompts")
    add("  the loop never touched and showed an 11% drop in sentence-length")
    add("  variance that disappeared once they were excluded.")
    add("")
    add("  Compare every gate delta against the noise floor printed under")
    add("  it. The control arm is a second ungated generation from the same")
    add("  prompt, so its delta is what this model varies by for no reason")
    add("  at all. A gate delta smaller than that is not a finding.")
    add("")
    add("  Compare the gate against REWRITE ALONE too. That arm spent the")
    add("  same generations on the same prompt and was told only to")
    add("  rewrite, never what was wrong. Whatever it gains is what a")
    add("  second pass gains. Only the distance between the gated arm and")
    add("  that one belongs to the flags.")
    add("")
    if "instructed" in _arms(rows):
        add("  Compare the gate against TOLD THE RULES hardest of all. That")
        add("  arm spent ONE generation with the enforced checks' own wording")
        add("  pasted into the prompt, the way a line in CLAUDE.md would")
        add("  arrive. It costs no hook, no install and no extra generation.")
        add("  Whatever it reaches is what this project competes against --")
        add("  not zero. A gate that only matches it buys nothing.")
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
