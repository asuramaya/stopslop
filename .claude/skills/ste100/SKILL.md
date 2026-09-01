---
name: ste100
version: 0.1.0
description: |
  Write or rewrite PROCEDURAL text (runbooks, installation and operating
  instructions, safety notes, error messages) so it passes stopslop's
  ASD-STE100 gate on the first attempt. Use ONLY for a file the project
  routes to the ste100 ruleset -- run `stopslop.py list-rulesets` if you are
  unsure, since ste100 is opt-in and most prose routes to slopwatch instead.
  Do not use for a README, a design note, or any prose meant to read like a
  person wrote it. Triggers: "STE100", "runbook", "procedure", "operating
  instructions", "safety notice", "error message".
license: MIT
compatibility: claude-code
metadata:
  standard: ASD-STE100 Issue 9 (2025-01-15)
  companion: stopslop src/pretool_hook.py -- this skill primes the
    draft; the hook is the actual gate. Priming reduces retries, it does
    not replace the gate.
---

# STE100 priming for stopslop

This is the priming layer, not the gate. The gate (`src/pretool_hook.py`)
is what actually enforces anything -- it denies writes with real violations,
full stop, regardless of whether this file was followed. This skill exists
only to cut the retry rate: get closer to compliant on the first draft so the
gate fires less.

Scope: this skill primes the `ste100` ruleset only. stopslop's gate now runs
three built-in rulesets (see the README's "Rulesets" section): `ste100`,
`slopwatch` for ordinary AI prose habits, and `codewatch` for the tells an
agent leaves in Python source. Neither of the other two has a priming skill
yet.

Everything below applies ONLY to a file a project explicitly routes to
`ste100` in `stopslop.config.json`. That is a narrower set than it used to
be. `ste100` is no longer any file's default: prose defaults to `slopwatch`,
`.py` to `codewatch`, and `.claude/` stays out of scope. ASD-STE100 is a
controlled language for PROCEDURES, so a project opts into it for runbooks
and instructions, not for a README or a design note -- the monotone it
enforces is wrong for those, and close kin to the flat register this project
exists to catch. If the file you are about to write is not routed to
`ste100`, none of the rules below govern it. Run `python3 stopslop.py list-rulesets` from the
repository root to see which ruleset a given path actually resolves to.

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

4. **`-ing` forms: one narrow exception, ban everything else** (3.5).
   Allowed: one of the ~9 dictionary-approved -ing nouns/adjectives
   (lighting, opening, routing, servicing, mating, missing, remaining), plus
   a short closed list of ordinary English words with no verb-derived
   reading at all (morning, ceiling, thing, and a few others -- not a
   general rule, just those exact words). There is no noun-compound
   exception: an -ing word used as a modifier inside a technical noun
   compound ("monitoring alerts", "operating temperature", "routing table")
   still gets flagged today -- a syntactic heuristic for that case was
   tried and reverted because it silently exempted genuine misuse too
   ("initiating failover" reads identically to "monitoring alerts" at the
   regex level). Treat every -ing word as banned unless you know it is one
   of the two lists above; the gate will over-flag legitimate compounds
   rather than miss real misuse. Everything else -- "before initiating
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
  don't rotate. The gate checks this document-wide today, not just per
  sentence, and denies the write if two members of the same rotation set
  both appear anywhere in the text.

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

It does not enforce the real approved-vocabulary list as a denial reason yet
(stopslop loads the actual extracted ASD-STE100 dictionary now, not a
stand-in -- see the README) -- an unapproved or unknown word is reported,
not blocked, until the project glossary matures enough to avoid new
friction on ordinary software vocabulary. Registered project terms
(`stopslop.py terms`) are exempt everywhere. It does not guarantee
compliance -- nothing does; see rule 9.1's own admission that some rewrites
need real semantic judgment no checklist can give you. It is a priming aid
to reduce gate retries, not a substitute for the gate.
