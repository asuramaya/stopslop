# Padding-set runs: does the gate teach writing, or teach avoidance?

Two runs, `run-2/` and `run-3/`, same eight `padding` prompts, same
model (`claude -p`, Claude Code 2.1.257), same `slopwatch` split of 11
enforced and 11 held-out checks. `run-3/` adds the arm that matters.

The earlier `technical` run found so few flags that the question could
not be asked. These prompts ask for register rather than content, so they
produce flags. Their flag rate is not a base rate for anything.

## The answer, as far as two runs can give one

**A plain "rewrite this" beat the gate on the checks the gate was not
enforcing, at the same cost.**

`run-3`, restricted to the four prompts where the gated loop actually
revised, with the blind arm and the gated arm each spending exactly two
generations:

| arm | enforced flags | held-out flags |
|---|---|---|
| ungated | 8 | 5 |
| control (second ungated sample) | 3 | 4 |
| blind (rewrite, told nothing) | 2 | **2** |
| gated (rewrite to clear the flags) | **0** | 4 |

Per 1000 words, against each arm's own baseline: the gate took held-out
flags from 4.81 to 3.93, a 18% drop. A second independent sample managed
26% by doing nothing at all. Rewriting with no information about what was
wrong managed 58%.

So the gate wins overwhelmingly on what it enforces, which it must, since
the loop runs until it does. On everything else it did worse than telling
the model "rewrite this" and worse than sampling twice.

The mechanism this suggests is the ordinary one. A revision aimed at a
named list of defects is a narrower act than a revision aimed at the
whole text. The named list gets fixed; attention goes there and not
elsewhere.

## Why this is not settled

**Four prompts.** The decisive comparison rests on 2 held-out flags
against 4. Every number on this page is single digits.

**The two runs disagree.** In `run-2`, which had no blind arm, held-out
flags fell 7 to 3 under the gate against 7 to 6 in the control, which
reads as the gate transferring. In `run-3` the same measurement was 5 to
4 against 5 to 4: no effect. The two runs also revised DIFFERENT prompts
-- only `case-study` appears in both -- because which draft trips a flag
is itself stochastic. Effects this size are inside run-to-run variation,
and only the blind-versus-gated comparison is internally controlled,
since both arms live in the same run on the same prompts with the same
compute.

**No flattening was found in either run.** Sentence-length variance moved
less under the gate than under sampling. An 11% drop that appeared in
`run-2`'s first rendering was an artifact of averaging in prompts the
gate never touched, and it disappeared when the report was corrected to
score only the prompts the loop revised.

**Nothing here measures whether the writing is good.** Read `texts/`.
Both arms are there for every prompt.

## What this supports

Narrowly, and only for this model on this kind of writing: the value the
gate adds over asking for a rewrite is unproven, and the two comparisons
that control for compute point the other way. A blocking gate costs a
generation per revision and buys a guaranteed-clean score on the checks
it names, at some cost to the ones it does not.

## What would settle it

The blind-versus-gated comparison at a defensible sample size. Same
design, 30 or more prompts that reliably trip flags, repeated runs to
average over which prompts happen to trip. That is a bigger experiment
than anything here, and it is the only one that would turn this from
suggestive into established.

Until then the honest summary of this project's own evidence is that its
central mechanism has not been shown to beat asking the model to try
again.

## Reproducing

`run-3/recordings/` replays exactly:

```
python3 src/evalab/run.py --replay evalab-runs/2026-09-01-padding/run-3/recordings --prompt-set padding
```

`run-2/recordings/` does not, and the refusal is correct rather than a
fault. That run predates the blind arm, so it recorded three generations
of each first prompt where the current harness asks for four. The
recorded generator raises instead of handing the fourth call an answer it
recorded for a different arm. The files are kept because they hold every
intermediate revision, which `texts/` does not.
