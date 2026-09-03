# codewatch: the experiment was wrong, and that is the finding

Ten code-writing prompts, the `codewatch` ruleset, four checks enforced
and six held out. The last ruleset in this project with no evidence at
all.

## The result is that there is no result

**The gated loop revised 0 of 10 prompts.** One flag fired across 2135
words of generated Python, and every arm scored 0 or 1 total. Nine of
codewatch's ten checks fired zero times.

By this project's own reading rules, that means the run measures nothing
but generation variance. It is reported anyway, because a null result
that gets quietly dropped is how a check set stays unexamined -- and
because the reason for the null is more useful than a number would have
been.

## Why the checks did not fire

Look at what codewatch catches: leftover `print()` calls, TODO stubs
with no issue behind them, comments narrating a refactor ("Phase 2:
now we..."), comments citing the plan or the ticket, generic names like
`helper_1`, a bare `except: pass`.

That is EDITING DEBRIS. It accumulates when an agent works a file over
many turns -- prints added to diagnose something and never removed, a
comment explaining what changed relative to what was there before, a
stub left where attention moved on. A one-shot "write me a rate limiter"
prompt produces none of it, because there was no previous state to
narrate and no debugging session to leave behind.

The prompt design was wrong for the ruleset. Not the ruleset.

## The evidence that codewatch works is in the gate log, not here

Eight live codewatch gate events on this repository. One of them is
`swallowed_exception`, and it fired **today, on this project's own
commit**: the first version of the atomic-write fix used
`except OSError: pass` to clean up a temp file, and the pre-commit hook
refused it. That was correct, and the code is better for it.

So codewatch catches things. It catches them during real iterative work,
which is exactly where the harness cannot currently look.

## What would actually measure it

A multi-turn arm: generate a module, then ask for three or four
successive changes to it, then judge the file. That is the shape of the
work codewatch was built for and the shape this harness has never run --
every arm here is one prompt and at most a few revisions of the same
text.

It is a real addition to the rig rather than a parameter change, and it
would apply to prose too: nobody has measured what a document looks like
after a model has edited it five times, which is how most documents
that matter get written.

## What this run does establish

`codewatch` should not be judged by this number, in either direction. It
is not evidence the ruleset works and not evidence it does not. What it
establishes is narrower and worth having: **one-shot generation does not
produce the defects codewatch targets**, so anyone reaching for it to
clean up freshly written code is reaching for the wrong tool.

## Reproducing

```
python3 src/evalab/run.py --replay evalab-runs/2026-09-02-codewatch/recordings \
    --prompt-set evalab-prompts/code.md --ruleset codewatch --enforce codewatch \
    --complement --combine all
```
