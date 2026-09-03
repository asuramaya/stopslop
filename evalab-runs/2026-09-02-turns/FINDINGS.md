# Documents over their whole life, on three models: 2026-09-02

Six documents, each written and then edited three times -- add a
section, rename the thing, cut it down. Every arm runs every turn. Run
on `opus`, `sonnet` and `haiku`, in `../2026-09-02-turns-opus/`,
`-sonnet/` and `-haiku/`.

Every earlier run in this repository measured a first draft. This one
measures a document the way documents are actually written.

## Pooled result

Three models times six documents is 18 paired observations. Six prompts
per model clears significance on nothing by itself; pooling is what makes
the comparison testable, and model is a blocking factor rather than a
variable of interest.

| comparison | totals | paired | p |
|---|---|---|---|
| complement + gate vs ungated | 8 vs 50 | 17-0 | 0.000015 |
| gate vs ungated | 17 vs 50 | 14-0 | 0.00012 |
| complement + gate vs gate | 8 vs 17 | 7-0, 11 tied | 0.016 |
| instructed + gate vs gate | 9 vs 17 | 8-1, 9 tied | 0.039 |
| complement alone vs ungated | 27 vs 50 | 12-4 | 0.077 |
| instructed alone vs ungated | 33 vs 50 | 10-6 | 0.45 |
| blind rewrite vs ungated | 50 vs 50 | 5-8 | 0.58 |

Cost: 6.50 generations for complement + gate against the gate's 8.56.
Cheaper and better, as in every single-turn run.

## The hypothesis that motivated this build is wrong

The multi-turn arm was built on a guess: that documents get sloppier as
they are edited, and that a gate's real advantage is resisting that.

Tells after each turn, ungated:

| model | t0 | t1 | t2 | t3 |
|---|---|---|---|---|
| opus | 8 | 17 | 18 | 11 |
| sonnet | 24 | 23 | 22 | 19 |
| haiku | 29 | 20 | 18 | 20 |

Two of three models get BETTER as the document is edited. Only opus
rises, and only in the middle before falling back. **Documents do not
generally drift**, and the reason I proposed for using a gate does not
survive contact with three models.

## What is true instead, and it is more interesting

An instruction alone works in a single turn and stops working across
several.

Single-turn, an instruction roughly halved total tells (107 to 60, and
88 to 74 on another model). Here, pooled across three models, instructed
alone scores 33 against ungated's 50 and does not clear significance --
10 wins to 6, p = 0.45. The complement instruction does better, 27
against 50, and only reaches p = 0.077.

The gate is unaffected: 17 against 50, 14-0, p = 0.00012.

The mechanism is not the document drifting. It is the INSTRUCTION
FADING. A rule stated once at the top of a session competes with
everything said since, and by the fourth turn it is one voice among
many. A hook does not care how long the conversation is -- it reads the
text at the moment of the write, every time.

So the gate's advantage over an instruction really does grow with
session length, which is what the build was for. The mechanism is the
opposite of the one guessed.

## What is flat, on every model

| arm | opus | sonnet | haiku |
|---|---|---|---|
| complement + gate | 2 2 1 2 | 1 1 1 1 | 5 5 5 5 |
| gate | 5 5 4 6 | 8 6 7 3 | 9 8 8 8 |
| ungated | 8 17 18 11 | 24 23 22 19 | 29 20 18 20 |

The combined arm is flat at a low number on all three, which is the only
shape worth having in a long session: a document that is acceptable at
every write rather than only at the end. Nothing else in the table holds
that line.

Base rates differ by a factor of three -- opus opens at 8 tells where
haiku opens at 29 -- which is the whole argument for measuring a check
set against the model you actually use rather than trusting this table.

## Limits

**Six documents per model.** Nothing clears significance within a single
model; every p-value above is pooled. Three models agreeing on an
ordering is real evidence, and it is not the same evidence as one model
measured thirty times.

**Four turns.** Real documents get edited more than that, and the
instruction-fading effect should get worse with length. Untested.

**One author, one machine, prompts I wrote.** Unchanged from every other
run here.

## Reproducing

```
for m in opus sonnet haiku; do
  python3 src/evalab/run.py --replay evalab-runs/2026-09-02-turns-$m/recordings \
      --prompt-set evalab-prompts/edited.md --enforce structural \
      --complement --combine all
done
```
