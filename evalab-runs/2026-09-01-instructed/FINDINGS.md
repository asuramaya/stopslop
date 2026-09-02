# The free alternative, finally measured: 2026-09-01

Thirty `padding` prompts, the `structural` preset (17 enforced checks),
five arms. The fifth is the one every earlier round routed around: the
enforced checks' own wording pasted into the prompt, one generation, no
gate, no hook. What a line in `CLAUDE.md` would do.

The published claim this project rested on -- a blind rewrite moves
structural tells from 75 to 75 while the gate moves them to 3 -- was true
and compared against the wrong alternative. Nobody installs a hook
because "rewrite this" failed. They would skip it because a sentence in a
config file is free.

## The result

| arm | generations | enforced | held-out | total tells | per 1k |
|---|---|---|---|---|---|
| ungated | 1 | 84 | 35 | 119 | 15.01 |
| control (2nd sample) | 1 | 81 | 30 | 111 | 14.06 |
| blind rewrite | 2.87 | 85 | 18 | 103 | 14.34 |
| **told the rules** | **1** | 45 | **17** | **62** | **8.42** |
| gated | 2.87 | **8** | 23 | **31** | **4.09** |

**Telling the model the rules, once, for free, does about half of what
the gate does.** 119 total tells to 62, winning on 22 of 30 prompts and
losing on 4, sign test p = 0.00053, bootstrap +1.90 per document (95% CI
+1.20 to +2.63).

**The gate still wins from there, and not narrowly.** 62 to 31, on 20 of
30 prompts against 4, p = 0.0015, +1.03 per document (95% CI +0.47 to
+1.60). Per 1000 words the separation is cleaner still: 25 wins to 5,
p = 0.00032.

Both effects are real. Neither cancels the other.

## What it costs to buy the second half

2.87 generations per document against 1. The instruction is free; the
gate is roughly three times the tokens, plus a hook, plus an install, and
23 of 30 documents reached a clean pass rather than all 30. That is the
trade in one line: **halve your tells for nothing, or quarter them for
3x the compute.**

## The part that argues against the gate

On the 14 checks nobody enforced, the instruction scored 17 and the gate
scored 23 -- the instruction is nominally better at the thing the gate is
supposed to teach. It is not a real difference (8 wins to 5 with 17 ties,
p = 0.58), so the honest statement is that they are indistinguishable on
held-out checks. But it kills a specific claim: the gate does not
generalize better than simply saying what you want. Everything it wins,
it wins on the checks it was pointed at.

Every round so far has shown the same thing. Whatever the
loop is not aimed at does not improve.

## What survives

The premise survives, smaller and better specified than before.

- Naming the defects works. Both interventions that name them beat both
  that do not, and a blind rewrite at 2.87 generations still achieves
  nothing (103 against 119 ungated, inside the control arm's own 111).
- Enforcement beats instruction. 45 enforced flags survive a stated rule;
  8 survive a gate. A model told a rule follows it about half the time.
- No flattening, again. Sentence-length variance ran 8.78 ungated, 9.06
  instructed, 9.02 gated, 7.90 blind. The blind rewrite flattens prose
  more than either intervention that names something.

## What this means for the project

The honest pitch is no longer "the gate cuts tells 72% where a rewrite
does nothing". It is: **a free line in CLAUDE.md gets you halfway, and
the gate is what closes the other half.** Anyone unwilling to spend 3x
the generations should take the instruction and skip the install. That
sentence belongs in the README, not in a findings file nobody opens.

## Reproducing

```
python3 src/evalab/run.py --replay evalab-runs/2026-09-01-instructed/recordings \
    --prompt-set padding --enforce structural
python3 src/evalab/stats.py evalab-runs/2026-09-01-instructed/result.json gated instructed
```

The run died at call ~258 of 264 -- `claude` exited 1 with an empty
stderr -- and was finished with `--resume`, which replayed the 258 saved
generations and generated the 4 that were lost. The recordings directory
is the whole run either way.
