# Enforcing shape, not just wording: 2026-09-01

Thirty `padding` prompts, four arms, 17 enforced checks instead of 11 --
the six document-shape checks added from Wikipedia's catalogue are in the
enforced set. Every one of the 30 tripped something, so all 30 rows carry
signal. 1323s at five workers.

## The result

| arm | enforced | held-out | total tells | per 1k |
|---|---|---|---|---|
| ungated | 75 | 30 | 105 | 13.31 |
| control | 80 | 34 | 114 | 14.36 |
| blind rewrite | 75 | 18 | 93 | 12.71 |
| gated | **3** | 26 | **29** | **3.79** |

**A blind rewrite moves structural tells from 75 to 75. The gate moves
them from 75 to 3.**

That is the finding, and it is the first thing measured in this project
that a rewrite cannot substitute for. Told only to rewrite, the model
reproduces the same document shape: the same bolded run-ins, the same
horizontal rules, the same uniform paragraph blocks, the same title-case
headings. It has no reason to think any of that is what gives it away.
Naming the defect is what moves it.

Total tells fall 72% against ungated and 69% against a rewrite at
identical compute. Paired across the 30 prompts, the gated arm carried
fewer total tells on 26, the blind arm on **zero**, with 4 tied. Sign
test p < 0.000001. Bootstrap 8.92 fewer flags per 1000 words, 95% CI
+6.61 to +11.30, favouring the gate in 100% of resamples.

Nothing else in this project's evaluation history has come close to that
separation. The two earlier rounds were directional at p = 0.12 and
p = 0.27; this is not close to the line.

## What it cost

2.9 generations per document, against 1.6 when only the lexical checks
were enforced. Enforcing shape means every document trips something, so
the gate always fires and always costs at least one revision. That is the
honest price of the result above.

Three enforced flags survived. Those documents hit the four-iteration
cap rather than converging, which is what the cap is for.

## What is still true from before

Held-out flags did not improve. The gated arm scored 26 against the blind
arm's 18 on the 14 checks nobody enforced, so the pattern from every
earlier round survives: whatever the loop is not pointed at does not get
better, and relative to a plain rewrite it gets slightly worse. That is
an argument for enforcing comprehensively rather than against enforcing
at all, and it is the reason the held-out split stays in the harness.

No flattening, again, and the direction is worth noting: sentence-length
variance ran 9.03 ungated, 8.61 gated, 8.07 blind. The blind rewrite
flattened prose more than the gate did.

## What this changes

The earlier rounds asked whether the gate beat asking the model to try
again, and could not show that it did. With only wording enforced, it
barely did: 25 total tells against a rewrite's 38, directional at best.
With shape enforced it is not a contest. The premise was sound and the
check set was covering the wrong layer.

## Reproducing

```
python3 src/evalab/run.py --replay evalab-runs/2026-09-01-structural/recordings \
    --prompt-set padding --enforce structural
```

`texts/` holds all four arms for all 30 prompts. The blind and gated
versions of the same prompt, read side by side, show the difference more
plainly than the table does.

## The human control, and what it shows about calibration

The earlier rounds said a real human baseline was the missing validation
and that no corpus was available offline. One was, in the interpreter
itself. CPython's stdlib module docstrings and a handful of pre-LLM
`.rst`/`.md` package docs (numpy's masked-array README, CPython's
`email/architecture.rst`, matplotlib and lazr documentation) are human
technical prose written years before any of this.

| corpus | structural flags /1k |
|---|---|
| CPython stdlib docstrings (8265 words) | 0.97 |
| human .rst/.md docs, pre-LLM (3831 words) | 2.09 |
| generated, ungated (8107 words) | 6.29 |
| generated, gated on structural | 0.39 |

Three to six times separation against text no model wrote. The checks are
not merely firing on everything.

They do fire on human prose sometimes: three thematic breaks, two copula
dodges, a triad and a uniform-paragraph run across the human markdown.
That is the correct behaviour for density signals rather than defect
detectors, and it is why all nine warn rather than block.

**The gate overshoots.** Gated output scores 0.39 per 1000 words, well
BELOW both human corpora. Text with no horizontal rules, no bold and
perfectly varied paragraph lengths is not what human documentation looks
like -- humans use all three, in moderation. Driving a signal to zero
when the human distribution sits at one to two per 1000 words does not
make text more human, it makes it differently artificial.

That is the next calibration: target the human band rather than zero, by
raising the thresholds until gated output lands inside it instead of
under it. It needs its own run to verify, and it is the clearest piece of
unfinished work this evaluation has produced.

Caveat on the control's size. Under 12000 words total across two genres,
and stdlib docstrings carry no markdown at all, so `bold_density`,
`thematic_break` and `title_case_heading` cannot fire there. The markdown
corpus is the fair comparison for those three and it is the smaller of
the two.
