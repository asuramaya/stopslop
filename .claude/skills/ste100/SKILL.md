---
name: ste100
version: 0.1.0
description: |
  Write or rewrite technical text (docs, READMEs, runbooks, error messages,
  release notes, incident reports) so it passes stopslop's ASD-STE100 gate on
  the first attempt. Use for documentation, error messages, and any text
  destined for a .md/.txt/.rst file in this project. Triggers: "STE100",
  "de-slop", "write docs", "runbook", "error message", "incident report",
  "release notes", "write clearly".
license: MIT
compatibility: claude-code
metadata:
  standard: ASD-STE100 Issue 9 (2025-01-15)
  companion: stopslop prototype/pretool_hook.py -- this skill primes the
    draft; the hook is the actual gate. Priming reduces retries, it does
    not replace the gate.
---

# STE100 priming for stopslop

This is the priming layer, not the gate. The gate (`prototype/pretool_hook.py`)
is what actually enforces anything -- it denies writes with real violations,
full stop, regardless of whether this file was followed. This skill exists
only to cut the retry rate: get closer to compliant on the first draft so the
gate fires less.

Rule text below is verified against the real ASD-STE100 Issue 9 spec
(`docs/ASD-STE100-rules-extracted.md` in this repo has the full extraction
with citations) -- not paraphrased secondhand.

## Step 1: classify

| | Procedural | Descriptive |
|---|---|---|
| Purpose | Tell the reader what to do | Explain what a thing is or does |
| Verb form | Imperative | Simple present/past/future |
| Sentence limit | 20 words (5.1) | 25 words (6.3) |
| Unit | One instruction per sentence (5.2) | One topic per paragraph, max 6 sentences (6.5/6.6) |

## Step 2: the checks that actually gate you (in priority order)

These map directly to what `pretool_hook.py` checks today. Get these right
and the gate passes clean.

1. **No `should`, `would`, `may`, `might`, `could`.** Not "usually rephrase" --
   never. The gate never auto-fixes these; it always stops and asks.
   - `should` → decide what you actually mean first: a hard requirement is
     "must"; a recommendation is either deleted or stated as fact ("X is
     faster because Y"). Do not leave "should" in and hope the reader infers
     which one you meant -- that ambiguity is the entire point of the rule.
   - `would` → restructure as a real conditional: "If X occurs, Y occurs,"
     not "Y would occur."
   - `may` / `might` / `could` (possibility) → normally "can". **Exception:
     never do this in front of `need to`, `want to`, `have to`, `wish to`,
     `like to`.** "may need to restart" does NOT become "can need to
     restart" -- that's not English. Restructure instead: "If X, restart Y."
     This is a real bug in other STE100 tools; don't repeat it.
   - `may` (permission) → "can".

2. **No present-perfect or present-perfect-passive.** "has completed", "have
   been terminated", "had already been reviewed" are all banned (3.2/3.4).
   Use simple past instead: "completed", "ended", "was reviewed" (name the
   actor if you can -- see passive voice below).

3. **Active voice, unless the actor is genuinely unknown** (3.6). "The system
   promoted the replica," not "the replica was promoted." If you don't know
   who/what did it, passive is legal -- but check that you really don't know,
   not that naming the actor is just inconvenient.

4. **`-ing` forms: two narrow exceptions, ban everything else** (3.5).
   Allowed: (a) one of the ~9 dictionary-approved -ing nouns/adjectives
   (lighting, opening, routing, servicing, mating, missing, remaining), or
   (b) an -ing word used as a modifier inside a technical noun compound
   ("monitoring alerts", "operating temperature", "routing table" -- the
   whole compound names one thing). Everything else -- "before initiating
   failover", "the file, ensuring integrity" -- gets rewritten: infinitive,
   simple tense, or a separate sentence.

5. **No contractions.** "doesn't", "it's", "there's" -- write it out.

6. **No semicolons.** Two sentences instead.

7. **Sentence length.** Count per Step 1's limit. If unsure, count. Long
   compound sentences with "and", "which", "since", "while" clauses are the
   usual cause -- split at the clause boundary, or turn "if X, [also do Y]"
   chains into a numbered list once you have 3+ steps.

## Step 3: structure

- **Condition before command** (5.4/7.2): "If the build fails, read the
  log," not "Read the log if the build fails."
- **One instruction per sentence** (5.2), unless two actions genuinely
  happen at the same time.
- **Safety/risk language**: state the command or condition first, then the
  consequence (7.2/7.3) -- never bury a warning after an explanation.
  "Do not run `--force` against production. It deletes rows that do not
  match the source," not "Running `--force` in some cases could delete
  data, so be careful."
- **One term per concept, all the way through** (1.11/9.4): pick one of
  check/verify/confirm/validate/ensure, one of config/settings/options, and
  don't rotate. The gate does not check this yet (no cross-sentence memory
  in v0.1) but it is a real STE100 rule and reviewers will notice.

## Untouchables

Never rewrite: code blocks, inline code, CLI flags, file paths, identifiers,
quoted error strings, product/API names. These are technical nouns (1.5) or
quoted text (8.6) and are exempt from the vocabulary rules by definition.

## Step 4: self-check before you finalize

Before you consider a draft done, scan it for:
- Every should/would/may/might/could -- resolved, not left in
- Every "has/have/had (been)" -- rewritten to simple tense
- Every passive construction -- actor named, or genuinely unknown
- Every `-ing` -- one of the two allowed cases, or rewritten
- Any contraction or semicolon
- Longest sentence -- under the Step 1 limit

If unsure whether something is compliant, that is the signal to restructure
rather than guess -- the gate catches a wrong guess anyway, but a self-check
avoids the retry.

## What this skill does not do

It does not enforce the ~875-word approved-vocabulary list (stopslop's
dictionary is a small stand-in, project-expandable by design -- see
`docs/ASD-STE100-rules-extracted.md`'s dictionary section). It does not
guarantee compliance -- nothing does; see rule 9.1's own admission that some
rewrites need real semantic judgment no checklist can give you. It is a
priming aid to reduce gate retries, not a substitute for the gate.
