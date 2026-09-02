# ste100, measured for the first time: 2026-09-02

Six `technical` prompts against the `ste100` ruleset, six checks
enforced (`ing_form`, `length`, `passive`, `perfect_tense`,
`punctuation`, `trailing_condition`) and seven held out.

This ruleset had never been evaluated. Every published number in this
repository is about `slopwatch`, while `ste100` is what actually fires
in production: across 77 live gate events its checks are the five
most-fired in the whole project -- vocabulary 32, ing_form 32, modal 30,
length 23, passive 21.

It went unmeasured because the harness failed silently. `ste100` shares
no check id with `slopwatch`, so every preset intersected it to nothing,
the gated arm never revised, and the report read "the loop revised 0 of
30 prompts" -- which looks like a null result about the gate rather than
a broken experiment. `split_checks` raises now.

## The result

| arm | generations | enforced | held-out | total flags |
|---|---|---|---|---|
| instructed | **1.00** | 10 | **371** | **381** |
| ungated | 1.00 | 26 | 385 | 411 |
| gated | 3.00 | **9** | 424 | 433 |

**The gate does not work on this ruleset.**

Against ungated it scores 433 flags to 411, paired 3-2 with one tie,
p = 1.0. Indistinguishable from doing nothing, at three generations per
document.

Stating the rules instead scores 381, and beats the gate on **all six
prompts, 6-0, p = 0.031**, for one generation. A clean sweep is a clean
sweep even at n = 6.

## What the gate is actually doing

Per check, across every arm:

| | ungated | instructed | gated |
|---|---|---|---|
| vocabulary | 380 | **364** | **419** |
| ing_form | 15 | 3 | 4 |
| length | 6 | 2 | 4 |
| synonym_rotation | 5 | 7 | 5 |
| passive | 3 | 1 | 0 |

The loop does what it is told: enforced flags fall 26 to 9. But
`vocabulary` -- which is 92% of every flag in this run, and which warns
and never blocks -- goes UP under the gate, 380 to 419, while the
instruction takes it DOWN to 364.

So the gate rewrites sentences to satisfy six structural rules and
reaches for non-approved words while doing it. It buys its enforced
score with the one signal nobody is watching, and that signal is
overwhelmingly the largest.

This is the sharpest version of a result every round has found: the loop
improves what it points at and nothing else. Here "nothing else" is
92% of the output.

## What this means for the project

`ste100` is opt-in and reaches no file until a rule names it, which was
already the right default. This run says something stronger: **routing a
file to `ste100` and letting the gate revise it makes the file worse by
that ruleset's own dominant measure.**

Two honest options, neither of them tested yet. Enforce `vocabulary`,
which the project has deliberately refused to do because a closed
875-word aerospace vocabulary fires constantly on software prose. Or use
`ste100` as an instruction rather than a gate, which this run says works
better and costs a third as much.

## Caveats that matter

**Six prompts.** The `technical` set, chosen for real content rather
than to produce flags. Every comparison rests on single-digit prompt
counts, and only the 6-0 sweep clears significance.

**One genre.** These are software-documentation prompts, not the
maintenance procedures ASD-STE100 was written for. A controlled language
for aircraft manuals evaluated on README sections is being asked a
question it was not designed to answer, and the vocabulary result is
partly that mismatch showing.

**`vocabulary` warns and never blocks**, so nothing here would have
denied a real write. The gate's damage is to a number, not yet to
anybody's file.

## Reproducing

```
python3 src/evalab/run.py --replay evalab-runs/2026-09-02-ste100/recordings \
    --prompt-set technical --enforce ste100 --ruleset ste100
python3 src/evalab/stats.py evalab-runs/2026-09-02-ste100/result.json \
    instructed gated
```
