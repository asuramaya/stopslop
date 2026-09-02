# Evaluation runs

Every number this project publishes comes from one of these directories.
Each holds the whole run: `result.json`, the rendered `report.txt`, the
generated text under `texts/`, the raw `recordings/` that replay it
without a model, and a `FINDINGS.md` written against that run alone.

Read them in order. The conclusions change between them, and the later
ones are not corrections of sloppy work in the earlier ones -- they are
what happens when a harness is allowed to answer the question it was
pointed at.

| run | what it asked | what it found |
|---|---|---|
| `2026-09-01/` | Does the gate change anything on real technical prose? | Almost nothing tripped a check. The question could not be asked at this base rate. |
| `2026-09-01-padding/` | Same question on prose chosen to produce flags. Two runs; `run-3` adds the blind-rewrite arm. | A plain "rewrite this" beat the gate on the checks nobody enforced, at the same cost. Four prompts, single digits, not settled. |
| `2026-09-01-padding30/` | The same comparison at 30 prompts, lexical checks enforced. | Directional at best. The lexical layer is nearly exhausted; a rewrite gets most of it. |
| `2026-09-01-structural/` | What if the gate is pointed at document shape instead of wording? | A blind rewrite moves structural tells 75 to 75. The gate moves them to 3. The first result a rewrite cannot substitute for. |
| `2026-09-01-instructed/` | Does the gate beat simply telling the model the rules, for free? | The instruction does about half the gate's work in one generation. The gate closes the other half for roughly 3x the compute. |

| `2026-09-02-leaderboard/` | Does the gate beat the tools people actually install? | It beats all three, every comparison under p = 0.05. It is also last on held-out checks, and its generated instruction ties the 16.7k-star hand-written one at p = 0.84. |
| `2026-09-02-combined/` | Does an instruction STACK with the gate, or compete with it? | It stacks, and costs less than the gate alone: 15 tells against 30, in 2.37 generations against 2.97. But only an instruction that names things the gate does not already enforce. |
| `2026-09-02-ste100/` | Does the gate work on the ruleset that actually fires in production? | No. 433 flags against ungated's 411, p = 1.0. An instruction beats it 6-0 for a third of the cost. |

The last two are the ones to read if you read only two. One says the
gate and an instruction should be used together rather than chosen
between. The other says the gate does not work on this project's
second ruleset.

## Replaying a run

```
python3 src/evalab/run.py --replay evalab-runs/<run>/recordings \
    --prompt-set padding --enforce structural
```

Match `--prompt-set` and `--enforce` to what the run's own `report.txt`
names, or the replay asks a question the recordings do not answer and
raises rather than guessing. `2026-09-01-padding/run-2/` does not replay
at all: it predates the blind arm and recorded three generations per
prompt where the harness now asks for five. The refusal is correct. Its
files are kept because they hold every intermediate revision, which
`texts/` does not.

## Rechecking a claim

```
python3 src/evalab/stats.py evalab-runs/<run>/result.json gated instructed
```

Paired by prompt: an exact two-sided sign test with ties dropped, and a
seeded percentile bootstrap on the mean paired difference. With no arms
named it compares the gated arm against every other one present.

## What none of this measures

Whether the writing is any good. Every metric here answers whether text
still reads as machine-written. Those are different questions, and the
saved `texts/` are the only evidence for the first one. Read them side by
side before believing any table.
