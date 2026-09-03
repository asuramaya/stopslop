# codewatch, measured properly at last: 2026-09-03

Six Python modules, each written and then changed three times -- make it
thread-safe, handle the exception that kills the thread, rename it
everywhere. Run on `opus` and `haiku`, in `../2026-09-03-codewatch-opus/`
and `-haiku/`.

Two earlier attempts at this were invalid and are deleted. This one
carries the three checks that make a null result mean something.

## Why this run can be believed

**The checks work.** A file written by hand containing all ten defects
trips all ten. So a low number is a fact about the code, not a broken
ruleset. This is the check the earlier attempts skipped, and without it
a table of zeros says nothing.

**The arms contain code.** 0 of 6 arms returned prose on either model.
The earlier runs linted the model's *summary of what it had done*,
because `claude -p` is an agent that writes the file and reports back.
Generations now run in a scratch directory and every prompt forbids
touching the filesystem.

**The turns are where debris comes from.** Not "write me a rate
limiter", which is a clean first draft with nothing to leave behind, but
four rounds of change on the same file.

## The result depends on the model, and that is the finding

Flags per 1000 words, ungated:

| model | rate |
|---|---|
| opus | 0.00 |
| haiku | 2.45 |

Opus produced **one** flag across 16089 words in six arms. Haiku
produced six across 6406, including two `print_debug` and two
`swallowed_exception` -- the one defect in this ruleset that blocks a
write.

So the honest statement is not "model-written code carries no debris".
It is that **the debris rate tracks model capability**. A stronger model
leaves almost none; a weaker one leaves some. Codewatch is worth running
against the second and close to free against the first.

The gate moves it in the right direction on haiku -- 2.45 ungated to
0.82 gated to 0.00 with an instruction alongside -- but on six flags
total that is a direction, not a result. Nothing here is significant and
nothing should be quoted as though it were.

## A check whose entire live output was wrong

Before the fix in this run, `constant_condition` accounted for nearly
every flag on opus. Every one was `while True:` in a queue worker or a
token-bucket refill.

`while True:` is the standard Python idiom for a loop that runs until
something breaks it. The check exists for dead code -- `if True:`,
`if False:` -- and was calling correct, conventional code a defect.

That is worse than a check that never fires. A silent check costs a
reader attention; a wrong one costs an afternoon and teaches them the
tool is noise. `while True:` is excluded now, `while False:` still
flagged, and the positive control still trips all ten checks.

Found only by reading what the flags actually matched. The count alone
looked like a modest, plausible signal.

## What codewatch is actually for

The debris is real. This project's own gate caught a bare
`except: pass` in its own commit on 2026-09-02 and refused it,
correctly, and there are eight live codewatch events in this
repository's history.

But that came from a model working iteratively inside a long session, in
a real repository, under pressure to make a test pass -- not from a
model asked to produce a module and hand it back. Those are different
activities and only one of them leaves a mess.

**Codewatch is not an anti-slop ruleset in the sense this project uses
the word.** It does not catch a fingerprint of machine authorship,
because machine-authored code does not have this fingerprint. It catches
debris from iterative editing, by anyone. That is a useful tool
documented as the wrong one, and the documentation is corrected rather
than the ruleset.

## Limits

**Six modules per model, six flags total on the noisier one.** Every
number here is single digits. Two models, one author, prompts I wrote.

**A first draft plus three changes** is still a short life for a file.
The debris this catches accumulates over the kind of session that
produces a hundred edits, and nothing here reaches that.

## Reproducing

```
for m in opus haiku; do
  python3 src/evalab/run.py --replay evalab-runs/2026-09-03-codewatch-$m/recordings \
      --prompt-set evalab-prompts/code-edited.md --ruleset codewatch \
      --enforce codewatch --complement --combine all
done
```
