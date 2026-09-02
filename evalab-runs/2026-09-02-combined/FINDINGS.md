# Instruction and gate together: 2026-09-02

Thirty `padding` prompts, the `structural` preset, eight arms. Two of
them are new: the same instruction that runs as a one-generation arm,
also stated up front inside the gated loop.

Every earlier round treated these as alternatives. They are not.

## The result

| arm | generations | enforced | held-out | total tells |
|---|---|---|---|---|
| stop-slop + gate | **2.37** | 2 | **13** | **15** |
| stopslop rules + gate | **2.03** | **1** | 22 | 23 |
| gate alone | 2.97 | 7 | 23 | 30 |
| stop-slop alone | 1.00 | 39 | 12 | 51 |
| stopslop rules alone | 1.00 | 36 | 18 | 54 |
| blind rewrite | 2.97 | 61 | 16 | 77 |
| control | 1.00 | 86 | 33 | 119 |
| ungated | 1.00 | 83 | 37 | 120 |

**They stack, and the combination is cheaper than the gate alone.**

stop-slop plus the gate reaches 15 total tells against the gate's 30,
paired 17-5 with 8 ties, p = 0.017. It spends 2.37 generations against
the gate's 2.97, because a document that starts closer to clean needs
fewer revisions to get there. Better and cheaper is not a trade-off, so
there is nothing to weigh: if you are running the gate, state the rules
too.

## Why one instruction stacks and the other barely does

stopslop's own generated block plus the gate reaches 23, which beats the
gate's 30 only directionally: 13-6 with 11 ties, p = 0.17. On held-out
checks it is indistinguishable from the plain gate, 22 against 23.

stop-slop plus the gate reaches 13 held-out flags against the gate's 23,
paired 13-3, p = 0.021.

The reason is visible in how the two instructions are built. This
project's block is generated from the enforced check table, so it names
exactly what the gate is already going to enforce -- the same information
twice, once before the write and once as a denial. stop-slop names other
things, including territory no check here enforces at all.

**An instruction that duplicates the gate adds nothing. An instruction
that covers what the gate does not, adds exactly that.** Which also
explains the last four rounds' standing result, that the gate never
improves held-out checks: nothing was ever telling it to.

## What this changes

The recommendation was "gate, or skill file if you will not spend the
generations". It is now: **do both, and prefer an instruction that is
not a restatement of your own enforced checks.**

The obvious follow-up is to generate the instruction from the HELD-OUT
half of the split rather than the enforced half, and see whether that
reproduces stop-slop's advantage from this project's own check table.
That is one run and it has not been done.

## Sentence variance

ungated 9.06, gate alone 8.35, stopslop rules + gate 9.41, stop-slop +
gate 7.85, stop-slop alone 7.79.

stop-slop flattens prose whether or not the gate runs, which is the same
result the leaderboard round found and the same caveat applies: no check
rewards or penalises that number, and flattening is a proxy for monotony
rather than proof of bad writing. The combined arm that keeps variance
highest is this project's own, at 9.41.

## Reproducing

```
python3 src/evalab/run.py --replay evalab-runs/2026-09-02-combined/recordings \
    --prompt-set padding --enforce structural --compare stop-slop --combine all
python3 src/evalab/stats.py evalab-runs/2026-09-02-combined/result.json \
    stop-slop+gated gated
```
