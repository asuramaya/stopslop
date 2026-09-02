#!/usr/bin/env python3
"""Paired comparisons between two arms of a saved run.

The 2026-09-01 structural findings quoted a sign test at p < 1e-6 and a
bootstrap CI that existed only in a transcript. A number nobody can
recompute is not evidence, so the arithmetic lives here now and any
saved result.json can be re-scored:

    python3 src/evalab/stats.py evalab-runs/<run>/result.json gated blind

Pairing is by PROMPT, which is the only thing the two arms share. Both
arms answered the same prompt in the same run, so the prompt's own
difficulty cancels and what is left is the arm.
"""
import json
import math
import random
import sys


def total_tells(row, arm):
    """Enforced plus held-out. The question this project actually cares
    about is whether the text still reads as machine-written, and a
    reader does not know which checks the loop was pointed at."""
    scores = row[arm]["scores"]
    return scores["enforced_flags"] + scores["held_out_flags"]


def per_1k(row, arm):
    scores = row[arm]["scores"]
    return scores["enforced_per_1k"] + scores["held_out_per_1k"]


def sign_test(pairs):
    """Two-sided exact binomial on wins vs losses, ties dropped.

    Deliberately the weakest test available: it assumes nothing about
    the distribution and ignores effect size. A result that survives it
    is not an artifact of a metric's shape.
    """
    wins = sum(1 for a, b in pairs if a < b)
    losses = sum(1 for a, b in pairs if a > b)
    ties = sum(1 for a, b in pairs if a == b)
    n = wins + losses
    if n == 0:
        return {"wins": wins, "losses": losses, "ties": ties, "p": 1.0}
    k = min(wins, losses)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n)
    return {"wins": wins, "losses": losses, "ties": ties,
            "p": min(1.0, 2 * tail)}


def bootstrap(pairs, resamples=10000, seed=0):
    """Percentile CI on the mean paired difference (b - a).

    Positive means the first arm carried fewer, i.e. the first arm won.
    """
    diffs = [b - a for a, b in pairs]
    if not diffs:
        return {"mean": 0.0, "lo": 0.0, "hi": 0.0, "favour_rate": 0.0}
    rng = random.Random(seed)
    means = []
    for _ in range(resamples):
        sample = [diffs[rng.randrange(len(diffs))] for _ in diffs]
        means.append(sum(sample) / len(sample))
    means.sort()
    return {"mean": sum(diffs) / len(diffs),
            "lo": means[int(0.025 * len(means))],
            "hi": means[int(0.975 * len(means)) - 1],
            "favour_rate": sum(1 for m in means if m > 0) / len(means)}


def compare(result, arm_a, arm_b, metric=total_tells):
    """arm_a against arm_b, paired by prompt."""
    rows = [r for r in result["rows"] if arm_a in r and arm_b in r]
    pairs = [(metric(r, arm_a), metric(r, arm_b)) for r in rows]
    return {"arm_a": arm_a, "arm_b": arm_b, "n": len(pairs),
            "total_a": sum(a for a, _ in pairs),
            "total_b": sum(b for _, b in pairs),
            "sign": sign_test(pairs),
            "bootstrap": bootstrap([(metric(r, arm_a), metric(r, arm_b))
                                     for r in rows])}


def render(cmp_result, metric_label="total tells"):
    a, b = cmp_result["arm_a"], cmp_result["arm_b"]
    s, bs = cmp_result["sign"], cmp_result["bootstrap"]
    out = [f"{a} vs {b}  ({metric_label}, paired over "
            f"{cmp_result['n']} prompts)",
            f"  totals            {a}: {cmp_result['total_a']}   "
            f"{b}: {cmp_result['total_b']}",
            f"  paired wins       {a} {s['wins']}, {b} {s['losses']}, "
            f"tied {s['ties']}",
            f"  sign test         p = {s['p']:.6g}",
            f"  mean difference   {bs['mean']:+.2f} in {a}'s favour "
            f"(95% CI {bs['lo']:+.2f} to {bs['hi']:+.2f})",
            f"  resamples favouring {a}: {bs['favour_rate'] * 100:.0f}%"]
    return "\n".join(out)


def main(argv=None):
    argv = list(argv if argv is not None else sys.argv[1:])
    if len(argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    path = argv[0]
    with open(path) as f:
        result = json.load(f)
    present = [a for a in ("ungated", "control", "blind", "instructed", "gated")
                if result["rows"] and a in result["rows"][0]]
    if len(argv) >= 3:
        pairings = [(argv[1], argv[2])]
    else:
        pairings = [("gated", other) for other in present if other != "gated"]
    for arm_a, arm_b in pairings:
        for label, metric in (("total tells", total_tells),
                               ("tells per 1k words", per_1k)):
            print(render(compare(result, arm_a, arm_b, metric), label))
            print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
