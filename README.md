# stopslop

[![tests](https://github.com/asuramaya/stopslop/actions/workflows/tests.yml/badge.svg)](https://github.com/asuramaya/stopslop/actions/workflows/tests.yml)

stopslop is a prototype of a pluggable text-enforcement gate for Claude Code. It does not check your documentation after you write it. It blocks a bad write before it happens, inside a live Claude Code session. ASD-STE100 (Simplified Technical English) is the first ruleset it enforces, not the only ruleset the engine can run.

Most AI output has a problem. It uses weak modals. It uses passive voice with no named actor. It uses jargon. It uses long sentences. ASD-STE100 exists to remove exactly this from human maintenance manuals. A linter that runs after the fact does not fix this well. By the time a reviewer reads the pull request, the bad text already shipped. Someone must notice it, flag it, and fix it. stopslop instead works at the point of the write. It intercepts most `Write`, `Edit`, and `Bash` file writes before they land on disk. It runs the text through the active ruleset's rule engine. Clean text passes through. A ruleset can auto-fix mechanical problems, like contractions and semicolons. A ruleset can deny text that needs real judgment, like an unnamed passive actor.

## Why this exists

ASD-STE100 is the aerospace industry's own answer to this exact problem, but for human writers, not AI ones. It has a closed vocabulary of about 875 approved words. It has a small set of grammar rules: one tense at a time, no complex verb constructions, no unclear pronouns. It has a length limit per sentence. The standard exists to make maintenance text clear across a global workforce, many of whom do not have English as a first language. It also fits an unrelated, newer problem well: it constrains a language model's tendency to write long sentences, weak modals, and passive voice. The two problems are not related. Both come from the same root cause: too much freedom in how you say something.

## Rulesets

ASD-STE100 is one ruleset, not the whole system. A ruleset is a small Python package under `src/rulesets/`. It plugs into the same gate, the same CLI, and the same MCP server. It supplies its own rules, its own auto-fix logic, and its own decision about what actually blocks a write. The gate itself does not know anything about ASD-STE100's vocabulary or grammar. It only knows how to call four required functions every ruleset supplies.

Three rulesets ship today:

- **`ste100`.** The ASD-STE100 rule engine described above. It also has a project glossary, so a user can register domain words the standard does not cover.
- **`slopwatch`.** Targets ordinary AI prose habits: an opener that stalls before the point, a dramatic colon reveal, an unnamed authority claim. It started as a small, original demo ruleset. It now also consolidates checks ported from several MIT-licensed prose linters, each one credited in NOTICE. ASD-STE100 erases individual voice on purpose, for one uniform result. `slopwatch` protects individual voice on purpose, against generic AI polish. The two rulesets aim in nearly opposite directions. The same gate runs both.
- **`codewatch`.** Targets the tells an AI agent leaves in Python source while it writes code. Examples: a comment that only restates the next line, a bare `except: pass`, a mutable default argument. It proves the plugin contract works past prose entirely. It ports checks from an MIT-licensed code-quality linter, credited in NOTICE.

A config file, `stopslop.config.json`, at the repository root, picks which ruleset applies to which file. Each rule is a glob pattern and a ruleset name, checked in order. The first match wins. Without this file, the gate falls back to the original defaults: `ste100` on `.md`, `.txt`, and `.rst` files, `.claude/` out of scope. See `stopslop.config.json.example` for the exact format.

Run `python3 stopslop.py list-rulesets` to see every registered ruleset, and which files route to each one under the current config.

## What it actually does

- **Real ASD-STE100 dictionary.** Not a hand-picked stand-in. The `ste100` ruleset loads the actual extracted dictionary: 787 approved words and 1204 forbidden words, most with an approved replacement. A team verified the extraction against the source PDF before it became enforcement data.
- **A live PreToolUse gate.** `src/pretool_hook.py` intercepts `Write`, `Edit`, and detected `Bash` file writes. It resolves the target path to a ruleset, then hands the text to that ruleset. Clean text passes through with no change. A ruleset can auto-fix mechanical violations, like contractions and semicolons. A ruleset can deny text that needs judgment, like a bad verb tense or an unnamed passive actor. It lists the specific violations, so an agent or a human can resolve them before the write proceeds.
- **A three-tier vocabulary model, for `ste100`.** Tier 1 is the real dictionary. Tier 2 is a project glossary (`src/rulesets/ste100/project-terms.json`). It covers domain words the standard does not have. Examples are "repository," "API," and "session." A user registers each word one at a time, with `stopslop.py register`, never in silence. Tier 3 is the forbidden-word-to-replacement map.
- **A memory loop, per ruleset.** The gate logs each decision and updates a short summary right away, not on a delay. The next session gets this summary as context, so an agent starts already aware of its own recent mistakes. Each ruleset gets its own summary file, since two rulesets can disagree about what a good sentence looks like.
- **Bash bypass detection.** The most obvious way around a `Write`/`Edit`-only gate is `cat > file.md <<EOF`. stopslop detects this. It detects a heredoc write through `cat` or `tee`, in either direction. It detects a quoted `echo`/`printf` write too. It also detects one piped through `tee`.
- **Integrity checks.** At each session start, the gate hashes its own code and every registered ruleset's own enforcement data. It compares the hash against the last known value. This makes an unexpected change to any of it visible.

## Setup

1. Run `python3 stopslop.py init`. This writes `.claude/settings.local.json` for your own clone location. It does not need any manual edit.
2. Start a Claude Code session inside the repository. The `SessionStart` hook reports any integrity problem. It also reports memory context from prior gate activity, for every ruleset with any.
3. Write something. If it is clean, it goes through. If it is not, the gate tells you right away, not later, in review.

## Commands

Once you wire up the gate, it runs on its own. You do not run it by hand. `stopslop.py` covers the other actions a person does directly. Every command below takes an optional `--ruleset ID`. Leave it out, and the command resolves a ruleset the same way the live gate does: from `stopslop.config.json`, or from the built-in defaults.

- `python3 stopslop.py init` sets up the hook for your own clone. Pass `--force` to replace the current setup.
- `python3 stopslop.py lint "some text"` checks text against the resolved ruleset. It does not write the text to any file. Use `--file PATH` to check a real file instead. Add `--all` to see every flag the engine can produce, not just the ones that will actually block a write today.
- `python3 stopslop.py register WORD "a short note"` adds a word to a ruleset's glossary, for a ruleset that has one.
- `python3 stopslop.py unregister WORD` removes a word from a ruleset's glossary.
- `python3 stopslop.py terms` lists every word in a ruleset's glossary, with its note.
- `python3 stopslop.py status` shows per-ruleset stats, recent gate activity, and whether the hook is even wired up yet.
- `python3 stopslop.py list-rulesets` lists every registered ruleset and the glob patterns routed to it.
- `python3 stopslop.py --version` prints the installed version.
- `python3 stopslop.py dashboard` opens the live web dashboard. Needs the venv.

## Dashboard (optional)

`python3 stopslop.py dashboard` opens a local page at `http://localhost:8501`, built with Streamlit. It shows live gate activity and per-ruleset stats. It has a lint playground that checks text against any ruleset without a real write. It has a routing-config editor and a glossary editor. It reads and writes the exact files the hook, the CLI, and an agent already use: `.claude/stopslop-history.log`, `stopslop.config.json`, each ruleset's own glossary file. One shared source of truth, not a second config store. A change here reaches the next gate call right away, with no session restart.

Setup shares the MCP tools' own venv (`requirements.txt` lists both dependencies):

1. If you have not already set one up for the MCP tools, run `python3 -m venv .venv`.
2. Run `.venv/bin/pip install -r requirements.txt`.
3. Run `python3 stopslop.py dashboard`.

## MCP tools (optional)

`src/mcp_server.py` exposes the same checks as MCP tools: `lint_text`, `check_word`, `register_project_term`, `unregister_project_term`, `list_project_terms`, `list_rulesets`, and `get_status`. A model can call these directly, with no Bash shell needed. Every tool takes an optional `ruleset` id, resolved the same way the CLI resolves one. A ruleset without a glossary or a word lookup returns a plain, structured refusal for the tools that need one, not an error.

This is not a second gate. It is a different kind of tool, on purpose. The hook sits in front of `Write` and `Edit`. It can deny a call before the write happens. The model must choose to call an MCP tool, or it never runs. A model can still write a file directly instead. No rule stops that. The MCP layer exists to cut down on denied attempts, not to replace the hook.

Setup needs a virtual environment, since `mcp` is this project's only external dependency:

1. Run `python3 -m venv .venv`.
2. Run `.venv/bin/pip install -r requirements.txt`.
3. Start a Claude Code session. `.mcp.json` is already in this repository. It wires the server up on its own.

## What it does not do

This is a prototype, not a finished product. Here is the honest gap list:

- Vocabulary enforcement is not a denial reason yet for `ste100`, on purpose. The real dictionary improves flag quality now. Unknown or forbidden words do not block a write yet. This waits until the project glossary is mature enough to avoid new friction on ordinary software vocabulary.
- The `ste100` dictionary does not track part of speech. The standard approves about 70 words in one part of speech. It forbids the same words in another part of speech. For example, the standard approves "check" as a noun. It forbids "check" as a verb. The checker only looks at the word, not its role in the sentence.
- Bash detection is deliberately conservative. It does not catch every write. `printf` with real format arguments, or a multi-line `cat >>` append with no heredoc, both pass through undetected.
- Each ruleset ships its own test suite. Run `python3 -m unittest discover -s src -p 'test_*.py'` from the repository root to run every one of them together. `test_stopslop.py`, at the repository root, covers the CLI's own ruleset-resolution logic directly. The file `src/test_pretool_hook.py` runs the live hook as a real subprocess. It uses a throwaway copy of the project, so it never touches this project's own real gate history. The file `src/test_mcp_server.py` covers the MCP server's tool functions directly. It needs the venv. Without `mcp` installed, the file skips cleanly. It does not fail.
- One file only ever routes to one ruleset. `stopslop.config.json` picks a single ruleset per glob pattern, first match wins. Two rulesets never both check the same write.
- Vocabulary auto-fix is off, on purpose, for every unapproved `ste100` word, not just the hard ones. An early version fixed a word to its one listed replacement with no check of the replacement's own part of speech. That silently broke real sentences. A person found this by hand, in this project's own README, not through any automated check. Real replacement-aware auto-fix needs new data this project does not have yet.

See `docs/incidents/` for a real incident this project had with its own gate, and the fix that followed.
