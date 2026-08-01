# stopslop

stopslop is a prototype of an STE100 Gatekeeper System (SGS). It does not check your documentation after you write it. It blocks a bad write before it happens, inside a live Claude Code session.

Most AI output has a problem. It uses weak modals. It uses passive voice with no named actor. It uses jargon. It uses long sentences. ASD-STE100 (Simplified Technical English) exists to remove exactly this from human maintenance manuals. A linter that runs after the fact does not fix this well. By the time a reviewer reads the pull request, the bad text already shipped. Someone must notice it, flag it, and fix it. stopslop instead works at the point of the write. It intercepts most `Write`, `Edit`, and `Bash` file writes before they land on disk. It runs the text through a real ASD-STE100 rule engine. Clean text passes through. The engine auto-fixes mechanical problems, like contractions and semicolons. The engine denies text that needs real judgment, like an unnamed passive actor.

## Why this exists

ASD-STE100 is the aerospace industry's own answer to this exact problem, but for human writers, not AI ones. It has a closed vocabulary of about 875 approved words. It has a small set of grammar rules: one tense at a time, no complex verb constructions, no unclear pronouns. It has a length limit per sentence. The standard exists to make maintenance text clear across a global workforce, many of whom do not have English as a first language. It also fits an unrelated, newer problem well: it constrains a language model's tendency to write long sentences, weak modals, and passive voice. The two problems are not related. Both come from the same root cause: too much freedom in how you say something.

## What it actually does

- **Real ASD-STE100 dictionary.** Not a hand-picked stand-in. The prototype uses the actual extracted dictionary: 878 approved words, 1319 forbidden words with approved replacements. A team verified the extraction against the source PDF before it became enforcement data.
- **A live PreToolUse gate.** `prototype/pretool_hook.py` intercepts `Write`, `Edit`, and detected `Bash` file writes. Clean text passes through with no change. The hook auto-fixes mechanical violations, like contractions and semicolons. The hook denies text that needs judgment, like a bad verb tense or an unnamed passive actor. It lists the specific violations, so an agent or a human can resolve them before the write proceeds.
- **A three-tier vocabulary model.** Tier 1 is the real dictionary. Tier 2 is a project glossary (`prototype/ste100-project-terms.json`). It covers domain words the standard does not have. Examples are "repository," "API," and "session." A user registers each word one at a time, with `stopslop.py register`, never in silence. Tier 3 is the forbidden-word-to-replacement map.
- **A memory loop.** The gate logs each decision and updates a short summary right away, not on a delay. The next session gets this summary as context, so an agent starts already aware of its own recent mistakes.
- **Bash bypass detection.** The most obvious way around a `Write`/`Edit`-only gate is `cat > file.md <<EOF`. stopslop detects this. It detects a heredoc write through `cat` or `tee`, in either direction. It detects a quoted `echo`/`printf` write too. It also detects one piped through `tee`.
- **Integrity checks.** At each session start, the gate hashes its own dictionary and code. It compares the hash against the last known value. This makes an unexpected change to the enforcement data visible.

## Setup

1. Run `python3 stopslop.py init`. This writes `.claude/settings.local.json` for your own clone location. It does not need any manual edit.
2. Start a Claude Code session inside the repository. The `SessionStart` hook reports any integrity problem. It also reports memory context from prior gate activity.
3. Write something. If it is clean, it goes through. If it is not, the gate tells you right away, not later, in review.

## Commands

Once you wire up the gate, it runs on its own. You do not run it by hand. `stopslop.py` covers the other actions a person does directly:

- `python3 stopslop.py init` sets up the hook for your own clone. Pass `--force` to replace the current setup.
- `python3 stopslop.py lint "some text"` checks text. It does not write the text to any file. Use `--file PATH` to check a real file instead. Add `--all` to see every flag the engine can produce, not just the ones that will actually block a write today.
- `python3 stopslop.py register WORD "a short note"` adds a word to the project glossary. It refuses a word the real dictionary already forbids unless you add `--override-unapproved "reason"`.
- `python3 stopslop.py status` shows dictionary size, glossary size, recent gate activity, and whether the hook is even wired up yet.

## What it does not do

This is a prototype, not a finished product. Here is the honest gap list:

- Vocabulary enforcement is not a denial reason yet, on purpose. The real dictionary improves flag quality now. Unknown or forbidden words do not block a write yet. This waits until the project glossary is mature enough to avoid new friction on ordinary software vocabulary.
- The dictionary does not track part of speech. The standard approves about 70 words in one part of speech. It forbids the same words in another part of speech. For example, the standard approves "check" as a noun. It forbids "check" as a verb. The checker only looks at the word, not its role in the sentence.
- Bash detection is deliberately conservative. It does not catch every write. `printf` with real format arguments, or a multi-line `cat >>` append with no heredoc, both pass through undetected.
- There is no automated test suite yet. A person verified each piece by hand, live, through the actual hook.
- Vocabulary auto-fix is off, on purpose, for every unapproved word, not just the hard ones. An early version fixed a word to its one listed replacement with no check of the replacement's own part of speech. That silently broke real sentences. A person found this by hand, in this project's own README, not through any automated check. Real replacement-aware auto-fix needs new data this project does not have yet.

See `docs/incidents/` for a real incident this project had with its own gate, and the fix that followed.
