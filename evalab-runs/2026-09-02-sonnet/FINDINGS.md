# The same experiment on different weights: 2026-09-02

Thirty `padding` prompts, the `structural` preset, eight arms -- the
same design as `2026-09-02-complement/`, generated with `--model sonnet`
instead of the default.

Every number this project had published came from one model on one
machine. This is the first that does not.

## The headline replicates

| arm | generations | total tells | opus | sonnet |
|---|---|---|---|---|
| complement + gate | 2.43 | 20 | 13 | 20 |
| instructed + gate | 3.03 | 36 | 26 | 36 |
| gate alone | 3.03 | 40 | 30 | 40 |
| complement alone | 1.00 | 63 | 77 | 63 |
| instructed alone | 1.00 | 74 | 60 | 74 |
| control | 1.00 | 86 | 107 | 86 |
| ungated | 1.00 | 88 | 107 | 88 |
| blind rewrite | 3.03 | 90 | 73 | 90 |

Three findings survive the change of weights, and they are the three the
project rests on.

**An instruction pointed at the gate's blind spot beats the gate.** 20
total tells against 40, paired 19-3 with 8 ties, **p = 0.00086**. On the
other model it was 13 against 30, 17-2, p = 0.0007.

**It fixes the held-out weakness.** 16 flags against the gate's 25,
paired 11-2, **p = 0.022**. The other model: 11 against 25, 14-2,
p = 0.004. Six rounds of "the gate improves what it points at and
nothing else" on one model, and the fix holds on a second.

**A blind rewrite still achieves nothing.** 90 against 88 ungated,
11-13 with 6 ties, p = 0.84 -- three generations spent, slightly WORSE
than one. The control arm is why that reads as noise rather than harm.

The ordering of the three gated arms is identical on both models:
complement + gate, then instructed + gate, then gate alone.

## What does not replicate

**"The complement instruction is the worst arm alone."** On the first
model it scored 77, behind every other instruction. Here it scores 63
and BEATS the plain instruction's 74. Neither difference is significant
(p = 0.48 here, and the other run's gap was not tested), so the honest
statement is that the two instructions are indistinguishable alone and
the earlier write-up over-read a single run's ordering.

The mechanism it was offered to illustrate is untouched -- an
instruction aimed at what the gate ignores stacks, one that repeats what
the gate enforces barely does -- but "worst alone, best combined" was
one model's arrangement, not a law. That claim is retracted.

## Base rates differ, and that is expected

Sonnet's ungated output carries 88 total tells to the other model's 107.
Different models have different habits, which is the whole reason a
check set needs measuring against the model you actually use. The
percentages are what travel: 77% here, 88% there, for the same
intervention.

## A methodological note worth carrying

`claude -p` is an AGENT, not a text completion endpoint. On the
`case-study` prompt this run wrote a file, `case-study-draft.md`, into
the output directory as well as returning the text. Nothing was lost --
the returned text is what got scored, and it matches -- but a harness
that shells out to an agent should expect side effects on disk and not
assume stdout is the only channel. The stray file was deleted; the run
is unaffected.

## Reproducing

```
python3 src/evalab/run.py --replay evalab-runs/2026-09-02-sonnet/recordings \
    --prompt-set padding --enforce structural --complement --combine all
python3 src/evalab/stats.py evalab-runs/2026-09-02-sonnet/result.json \
    complement+gated gated
```

The recorded generator version carries the model, so a replay can always
say which weights produced it.

## What this still is not

Two models on one machine, run by the author of the tool, on prompts the
author wrote. It removes the weakest version of the objection -- that
these are facts about one model's habits -- and leaves the rest of it
standing.
