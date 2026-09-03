---
name: slopwatch
version: 0.2.0
description: |
  Write or rewrite prose so it does not read as machine-written -- READMEs,
  docs, changelogs, posts, release notes. Removes the formatting habits that
  give generated text away: bold used as a running label, horizontal rules
  between sections, uniform paragraph blocks, title-case headings, the colon
  reveal. Use for any file the project routes to the slopwatch ruleset. Do
  NOT use for a runbook or operating procedure -- those route to ste100,
  which wants the opposite register. Triggers: "slop", "AI writing", "sounds
  like AI", "README", "docs", "changelog", "blog post", "release notes".
---

# slopwatch

This is the free half of stopslop, and the project measured what it is
worth before shipping it.

Across 30 prompts, stating these rules up front cut total AI-writing
tells from 107 to 60 in one generation. The blocking gate reached 30, for
about 2.8 generations per document. So this file does roughly half the
work for none of the cost.

Measured against the most popular tools in this category on the same
prompts, a block generated straight from the check table scored 58 where
stop-slop (16.7k stars) scored 54 -- paired 13-11 with 6 ties, p = 0.84.
Indistinguishable. Careful wording is not the active ingredient; naming
the specific defect is.

Full evidence: `evalab-runs/2026-09-02-complement/FINDINGS.md`.

## If you also run the gate, use a different block

This one is generated from every check, which means it repeats what the
gate is already going to enforce. Measured, that barely helps: 26 total
tells against the gate's 30, p = 0.17, and no improvement at all on the
checks nobody enforced.

A block generated from the checks the gate does NOT enforce reached 13 --
beating the gate alone 17-2, p = 0.0007 -- and took held-out flags from
25 to 11, the first time that number moved in six rounds. Regenerate with:

```
python3 stopslop.py rules --ruleset slopwatch --complement
```

A gate enforces; an instruction generalises. Pointing both at the same
targets wastes the instruction.

## What actually gives generated prose away

Four checks did most of the work in measurement: bold as body emphasis,
horizontal rules, uniform paragraph blocks, and the colon reveal. The
wording tells that older catalogues focus on barely fire any more --
across 59902 words of ungated generation, 19 of 31 checks fired zero
times. If you remember nothing else, remember the four.

## The rules

- Generator scaffolding left in: oaicite, [cite: 1], placeholders -- finish the text and read it
- The "it's not X, it's Y" construction -- just state Y
- A bolded word opening a list item as a per-item tag -- reserve bold for a rare callout
- Bold used as body emphasis throughout -- reserve bold for a rare callout
- A short rhetorical question with a canned answer -- collapse into one direct statement
- Short buildup, then a reveal: "The best part: it learns." -- state it as a plain sentence
- Saying "is" the long way: serves as, boasts, functions as -- use the plain verb
- One-line dramatic fragments: "That's it. That's the whole thing." -- cut them, the preceding sentence already made the point
- Em dashes clustering in one document -- most drafts need 0-2; use commas, periods or parentheses for the rest
- Emoji or decorative checkmarks in body text -- cut them
- An em dash, section sign or middle dot written as an HTML entity -- write the plain character
- Throat-clearing openers: "needless to say", "at the end of the day" -- state the point directly from the first sentence
- Filler verbs: leverages, facilitates, unlocks -- use a plain verb, or cut the sentence
- Fake ID tags opening list items: "R-1.", "US-01" -- number the list plainly
- A snake_case identifier written as plain prose -- name it in words, or mark it as inline code
- Marketing adjectives: seamless, robust, cutting-edge -- say what is actually true
- Marketing cliches: "hidden gem", "let's dive in" -- say the specific thing
- The "Not X. Not Y." listing construction -- state the point once
- The "not just X but Y" construction -- make the point once
- Body paragraphs nearly identical in length -- vary them with what each paragraph has to do
- A significance clause bolted to a sentence: ", underscoring the..." -- delete it, or make it a claim with something behind it
- Three parallel -ing items in a series -- keep the one that carries information
- Stock section skeleton: "Despite its success", "Looking ahead" -- name the specific thing the section is for
- Fake-humility feedback requests: "would love your feedback on this" -- cut them
- Standalone filler adverbs: undoubtedly, arguably, notably, importantly, ultimately -- most add nothing; cut them unless one is carrying real emphasis
- A banned synonym of one of this project's canonical terms, per its declared lexicon -- one word, one meaning: use the canonical term the word's own note names
- Horizontal rules dropped between sections -- headings already separate sections
- Headings Capitalised Like This -- sentence case
- Dramatic turning points with nothing concrete behind them: "Everything changed." -- name the actual event, or cut it
- Vague intensifiers with no number behind them: very, really, quite, significantly -- say how much, or cut the word
- Unnamed authority: "studies show", "experts agree" -- name the actual source, or cut the claim

## Regenerating this file

These rules come from the ruleset's own check table and go stale when it
changes:

```
python3 stopslop.py rules --ruleset slopwatch --quiet
```

## When this is not enough

This file is instructions. A model can ignore instructions, and the
measurement says it partly does -- 46 enforced flags survive a stated
rule, 5 survive a gate. If the text matters, install the hook:

```
python3 stopslop.py init
```

One honest caution, measured on this project's own numbers: a skill file
generalises BETTER than a gate. On checks nobody enforced, the gate
scored 25 flags against a skill file's 13 to 18. A gate improves what it
points at, and only that -- which is why the complement block above
exists.
