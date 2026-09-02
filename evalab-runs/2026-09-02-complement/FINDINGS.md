# Point the instruction at the gate's blind spot: 2026-09-02

Thirty `padding` prompts, the `structural` preset, ten arms. The new one
is COMPLEMENT: an instruction generated from the checks the gate does
NOT enforce, run alone and again inside the gated loop.

The previous round found that this project's own generated block barely
stacks with its own gate, while stop-slop stacks well. The proposed
reason was that the block is generated FROM the enforced check table, so
it tells the model exactly what the gate is about to enforce anyway.
This tests that directly.

## The result

| arm | generations | enforced | held-out | total tells |
|---|---|---|---|---|
| complement + gate | 2.77 | **2** | **11** | **13** |
| stop-slop + gate | 2.43 | 5 | 14 | 19 |
| stopslop rules + gate | 2.43 | 5 | 21 | 26 |
| gate alone | 2.80 | 5 | 25 | 30 |
| stop-slop alone | 1.00 | 37 | 13 | 50 |
| stopslop rules alone | 1.00 | 46 | 14 | 60 |
| blind rewrite | 2.80 | 71 | 20 | 73 |
| **complement alone** | 1.00 | 66 | 11 | **77** |
| ungated | 1.00 | 71 | 36 | 107 |

**The complement instruction is the WORST intervention alone and the
BEST in combination.**

Alone it scores 77, behind every other instruction and barely ahead of a
blind rewrite. Of course it does: it names only checks that fire rarely,
and says nothing about the four that carry most of the flags.

Combined with the gate it reaches 13 total tells, beating the gate alone
17-2 with 11 ties, **p = 0.0007**. Against the other combined arms it
beats stopslop's own enforced-set block 14-3 (p = 0.013), and leads
stop-slop's 19 without separating from it (10-5 with 15 ties, p = 0.30).

## The gate's oldest weakness, fixed

Five consecutive rounds found that held-out checks never improve: the
gate improves what it points at and nothing else.

| arm | held-out flags |
|---|---|
| gate alone | 25 |
| complement + gate | **11** |

Paired, 14-2, **p = 0.004**.

Nothing about the loop changed. The only difference is that something is
finally telling the model about the checks the loop was never aimed at.
The weakness was never intrinsic to gating -- it was a gap nobody had
filled, and it stayed invisible for five rounds because every
instruction tested was pointed at the same place the gate was.

## What this is, stated plainly

A gate and an instruction are good at opposite things. A gate enforces:
it will not stop until its checks pass, and it takes enforced flags from
71 to 2. An instruction generalises: it costs one generation and reaches
things no check is watching.

Pointing both at the same targets wastes the instruction. Pointing the
instruction at what the gate ignores is worth more than any other
change measured in this project's history.

## What it costs

2.77 generations against the gate's 2.80. Free, within noise. The
instruction is longer, which costs input tokens, and that is the whole
bill.

## What this changes in the tool

`stopslop.py rules` currently prints every enabled check, which is the
arm that barely stacks. It should print the COMPLEMENT of whatever the
gate will actually deny on, and say why.

## Caveats

**One prompt set, one model, 30 prompts.** The complement-versus-
stop-slop comparison does not separate (p = 0.30), so "generated beats
hand-written" is not supported -- only "generated matches it".

**The split is this harness's, not a user's.** `structural` enforces 17
of 31 checks. A project whose gate blocks on a different set gets a
different complement, which is the point, but it also means the 13 here
is not a number anyone else should expect to reproduce exactly.

**Sentence variance** ran 8.99 ungated, 8.28 for the combined arm,
8.68 for the gate alone. No flattening beyond the noise the other arms
show.

## Reproducing

```
python3 src/evalab/run.py --replay evalab-runs/2026-09-02-complement/recordings \
    --prompt-set padding --enforce structural --compare stop-slop \
    --combine all --complement
python3 src/evalab/stats.py evalab-runs/2026-09-02-complement/result.json \
    complement+gated gated
```

The live run died once at call ~480 of 547 and was finished with
`--resume`: 480 replayed, 67 newly generated.
