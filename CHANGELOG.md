# Changelog

## 0.2.1 -- 2026-09-03

Documentation only. Checking the docs against the tool rather than
assuming, and finding drift in both directions.

- The README documented `stopslop.py options`, removed weeks ago. A
  reader following it got an argparse error from the tool that told them
  to run it.
- It never mentioned `rule-checks`. A test now holds both directions:
  every registered command appears in the README, and the README names
  none that does not exist.
- The harness section was missing `--model` and `--combine`.
- The harness docstrings still described a five-arm single-turn
  experiment, with no mention of what the multi-turn arm found.

## 0.2.0 -- 2026-09-03

The release where the tool started measuring itself, and kept losing.

0.1.0 was a gate with a check set and a claim. This one has sixteen
committed runs across three models, every p-value recomputable from a
saved result, and four published findings retracted after better
measurement. The retractions are the point: nothing else in this
category can be wrong in public, because nothing else in it measures.

### The headline changed twice

An instruction pointed at the checks the gate does NOT enforce, run
alongside the gate, beats the gate alone -- and costs less, because a
draft that starts closer to clean needs fewer revisions. 13 total
AI-writing tells against 30, paired 17-2, p = 0.0007. It replicates on
three models and across a document's whole life.

`stopslop.py rules --complement` prints that instruction. `init` now
tells you to, because a gate on its own is the worst configuration
measured here.

### Retracted

- A flattening effect that was an averaging artifact over prompts the
  gate never touched.
- A `calibrated` preset that dropped four checks for firing more on
  human prose. They do not: the control was mostly CPython docstrings,
  which carry no markdown. Withdrawn, and the comment block stays where
  the preset was.
- Both codewatch runs, which linted the model's summary of what it had
  done rather than the code. `claude -p` is an agent.
- "The complement instruction is the worst arm alone" -- one model's
  arrangement, not a law.

### New

- `rules [--complement]` -- the instruction block, generated from the
  check table.
- `decay [--against CONTROL] [--calibrate]` -- which checks fire, which
  never do, and which fire MORE on prose you want to sound like. Two
  control genres are required before a verdict counts, because one
  corpus nearly cost a good check: `colon_reveal` reads 1.0x against
  code documentation and 25.8x against encyclopedia prose.
- `import --vale DIR` -- other people's rules. 17 of 17 from
  vale-ai-tells, 42 of the Microsoft Writing Style Guide's 44 real ones.
- `rule-checks` -- per-routing-rule thresholds and exemptions.
- `src/evalab/` -- the harness: eight arms, custom prompt sets, custom
  skill files, `--model`, multi-turn documents, paired statistics.
- A skill at `.claude/skills/slopwatch/`, carrying its own numbers.

### Changed

- `Check.kind` declares `tell` or `defect`, which decides what a
  check's silence means. Anything that blocks a write must be a defect.
- `codewatch` is documented as what it is: debris from iterative
  editing, by anyone, not a fingerprint of machine authorship.
- `constant_condition` no longer flags `while True:`. Its entire live
  output was that false positive.
- Config writes are atomic.
- Generations run sandboxed, because an agent writes files where it is
  started and this one wrote twenty into the repository root.

### Known

`ste100`'s gate is indistinguishable from doing nothing (p = 1.0). Most
checks fire zero times. Every number here comes from one author, one
machine, and prompts that author wrote.
