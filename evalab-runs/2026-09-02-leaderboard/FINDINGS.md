# The category, measured against itself: 2026-09-02

Thirty `padding` prompts, the `structural` preset, eight arms in one
run. Three of the arms are other people's tools, vendored under
`src/evalab/interventions/` with their licenses and used in full.

As far as I can find, this is the first time any of these has been
measured against a control. Every project in this space asserts that it
removes AI writing patterns. None publishes a number. That is not
carelessness on their authors' part -- there was no rig.

## The leaderboard

| arm | generations | enforced | held-out | total tells | per 1k | sentence stdev |
|---|---|---|---|---|---|---|
| gated | 2.93 | **8** | 26 | **34** | **4.39** | **9.26** |
| stop-slop (16.7k stars) | 1.00 | 42 | 12 | 54 | 7.39 | 7.07 |
| anti-slop-writing | 1.00 | 48 | 10 | 58 | 7.92 | 8.82 |
| stopslop `rules` | 1.00 | 41 | 17 | 58 | 7.84 | 8.49 |
| no-ai-slop (6.6k stars) | 1.00 | 57 | 11 | 68 | 9.49 | 7.81 |
| blind rewrite | 2.93 | 63 | 24 | 87 | 12.01 | 8.01 |
| control (2nd sample) | 1.00 | 81 | 30 | 111 | 14.20 | 9.11 |
| ungated | 1.00 | 80 | 34 | 114 | 14.56 | 8.70 |

## Three findings, and only one of them flatters this project

### 1. The gate beats every skill file, at three times the cost

Paired over the same 30 prompts:

| gated vs | wins | losses | ties | p |
|---|---|---|---|---|
| stop-slop | 17 | 5 | 8 | 0.017 |
| anti-slop-writing | 18 | 7 | 5 | 0.043 |
| stopslop `rules` | 17 | 3 | 10 | 0.0026 |
| no-ai-slop | 19 | 5 | 6 | 0.0066 |
| blind rewrite | 24 | 2 | 4 | 1.0e-05 |

Every comparison clears p < 0.05. The gate spends 2.93 generations per
document to do it; every skill spends one.

### 2. A generated instruction ties the 16.7k-star hand-written one

stop-slop scored 54 total tells, the block `stopslop.py rules` generates
straight from check metadata scored 58. Paired: **13 wins to 11 with 6
ties, p = 0.84.** They are indistinguishable.

That is worth more than it looks. stop-slop is the most-starred artifact
in this category and has been read and revised by thousands of people. A
block assembled mechanically from a check table matches it. Whatever
either is doing, careful wording is not the active ingredient.

### 3. Every skill file generalises better than the gate

On the 14 checks nobody enforced, the gate is LAST:

| arm | held-out flags | vs gated |
|---|---|---|
| anti-slop-writing | 10 | 17-3, p = 0.0026 |
| no-ai-slop | 11 | 16-3, p = 0.0044 |
| stop-slop | 12 | 14-3, p = 0.013 |
| stopslop `rules` | 17 | 14-6, p = 0.12 |
| gated | 26 | -- |

This is the fifth consecutive round showing the gate improves what it
points at and nothing else, and the first where the comparison is
against real alternatives rather than a straw arm. A skill file changes
how the model writes; a gate changes what survives the loop. On anything
the loop was not aimed at, the skill wins, and that is not close.

## What stop-slop buys its score with

Sentence-length variance, ungated 8.70. stop-slop 7.07, flattening on
25 of 30 prompts, **p = 0.0003**. It has the lowest variance of any arm
in the run, including the blind rewrite.

The gated arm ran 9.26, above the ungated baseline.

Flattening is a proxy for monotony, not proof of bad prose, and no check
in this project rewards or penalises that number -- which is exactly why
it is worth watching. Read `texts/` before concluding anything from one
statistic. But the direction is clear enough to state: the most popular
tool in this category makes every sentence more nearly the same length,
and nothing in it would tell its users that.

## The honest summary

For a writer who will spend the generations, the gate is the best
instrument measured here and the evidence is not marginal.

For everyone else, a skill file gets roughly half the way for one
generation, and which skill barely matters -- stop-slop, this project's
own generated block and anti-slop-writing are within four tells of each
other across 7300 words. Pick whichever installs most easily.

And if what you want is prose that reads well on the checks nobody
thought to enforce, the skill files are measurably better than the gate.

## Reproducing

```
python3 src/evalab/run.py --replay evalab-runs/2026-09-02-leaderboard/recordings \
    --prompt-set padding --enforce structural --compare all
python3 src/evalab/stats.py evalab-runs/2026-09-02-leaderboard/result.json gated stop-slop
```

The live run died once, at call 35, on every competitor arm at the same
time: a skill file opens with YAML front matter and the prompt was going
on argv, so `claude -p ---\nname: stop-slop...` read the text's own first
line as a command-line option. The prompt goes on stdin now. `--resume`
finished the run from its 90 surviving generations.

## What this does not measure

Whether any of this writing is good. Every number here answers whether
text still reads as machine-written. The saved `texts/` hold all eight
arms for every prompt and they are the only evidence for the other
question.
