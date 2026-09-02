# stopslop

[![tests](https://github.com/asuramaya/stopslop/actions/workflows/tests.yml/badge.svg)](https://github.com/asuramaya/stopslop/actions/workflows/tests.yml)

A pluggable text gate for Claude Code that reads your prose at the moment of the write, and an evaluation harness that measures whether the gate is worth running. The harness is the unusual part. Most tools in this category assert that they remove AI writing tells; this one tests the claim against a control, and the answer is narrower and stranger than the pitch would be.

## What the evidence says

Three rounds of 30 prompts, four arms each, all replayable from [`evalab-runs/`](evalab-runs/). The arm that matters is a **blind rewrite**: the same prompt, the same number of generations the gated arm spent, told only to rewrite and never what was wrong. Anything a plain rewrite achieves is not worth building a gate for.

**A blind rewrite moves structural tells from 75 to 75. The gate moves them from 75 to 3.**

That is the finding. Told only to rewrite, a model reproduces the same document shape, because nothing tells it the shape is what gives it away. Total tells fell 72%, the gated arm carried fewer on 26 of 30 prompts and the blind arm on zero, sign test p < 0.000001, favouring the gate in 100% of bootstrap resamples. It costs 2.9 generations per document.

Four things qualify that, and they are the reason to trust it:

- **It only works when the checks are pointed at formatting.** With just the 11 wording checks enforced, the gate barely beat a rewrite: 25 total tells against 38, directional at best. The lexical layer is nearly exhausted.
- **Four checks did the work, not seventeen.** Bold as body emphasis, horizontal rules, uniform paragraph blocks and the colon reveal. Five of the nine checks added from Wikipedia's catalogue of AI tells fire *zero times* across 8107 words of exactly the register they describe.
- **Tell sets decay.** The rule of three, copula avoidance and the participial significance clause were all catalogued against 2023-24 output. This model does not produce them at a measurable rate. What survives is the markdown habit, which is what [the stylometry work](https://arxiv.org/pdf/2603.27006) predicted would be the last fingerprint.
- **The gate overshoots.** Against a human control of CPython stdlib docstrings and pre-LLM package documentation, generated prose scores 6.29 structural flags per 1000 words and human prose 0.97 to 2.09. Gated output lands at 0.39, *below* the human band. Humans use bold and horizontal rules in moderation; driving a signal to zero does not make text human, it makes it differently artificial. Calibrating to the human band is the clearest unfinished work here.

And one thing that stayed true in every round: **held-out checks never improve.** Whatever the loop is not pointed at does not get better. That argues for enforcing comprehensively, not for skipping the gate, and it is why the harness always holds a subset back.

None of this measures whether the writing is *good*. It measures whether it still reads as generated. Those are different questions and only the second is answered here.

## What it actually does

A `PreToolUse` hook. Before Claude Code writes or edits a file, the hook gets the text, resolves the path to a ruleset through `stopslop.config.json` (first glob match wins), lints it, and either passes it, auto-fixes mechanical problems, or denies the write with the list of what to fix. A `pre-commit` hook gates the staged tree, ratcheted against HEAD.

It is not a security boundary and does not see every write path. [SECURITY.md](SECURITY.md) is specific about what it misses.

## Rulesets

A ruleset is a small Python package under `src/rulesets/` supplying three functions (`lint_and_gate`, `blocking_semantic_flags`, `apply_mechanical_fixes`) and three attributes. The gate knows nothing else about it. See [docs/adding-a-ruleset.md](docs/adding-a-ruleset.md) for the contract.

- **`slopwatch`** -- the default for prose, 31 checks. AI writing tells: wording habits, and the formatting habits that outlast them. Every check warns; none blocks.
- **`codewatch`** -- `.py` files, 10 checks. The tells an agent leaves in source. Blocks one thing, `swallowed_exception`, because a bare `except: pass` is a defect rather than a tell.
- **`ste100`** -- ASD-STE100 Simplified Technical English, 13 checks, 12 of them blocking. **Opt-in: it reaches no file until a rule names it.** It is a controlled language for maintenance procedures, and it buys precision with a deliberate monotone. Right for a runbook, a category error for a README -- this tool proved that on itself, flagging 23 sentences of `SECURITY.md` over the words "blocking", "warning" and "reading".

Defaults with no config file: `slopwatch` on `.md`/`.txt`/`.rst`, `codewatch` on `.py`, `.claude/` out of scope. Route procedures to `ste100` by name, above the general rule. This repository routes exactly one file that way.

The block/warn split follows one rule: a check blocks when it catches a **defect**, and warns when it catches a **tell**. A tell is a correlate, and text that dodges all 31 and says nothing still passes.

## Quickstart

1. Clone the repository, then run `python3 stopslop.py init`. This writes `.claude/settings.local.json` for your own clone location, installs a git pre-commit gate, and sets up the virtual environment the optional MCP tools and dashboard need (`python3 -m venv .venv`, then `pip install -r requirements.txt`) -- no manual edit needed for any of it. Pass `--no-venv` to skip that last, optional part.
2. Start (or restart) a Claude Code session inside the repository. **The first time, Claude Code asks whether to allow this project's MCP servers (`.mcp.json`) -- say yes.** Miss this and the MCP tools, and the dashboard they auto-start, silently never connect; nothing else in this setup depends on it. The `SessionStart` hook also reports any integrity problem, and memory context from prior gate activity, for every ruleset with any.
3. Run `python3 stopslop.py status` afterward. It reports the hook, the pre-commit gate, the virtualenv, and MCP trust each as their own state, with the exact command to fix anything not there yet. Inside the session, `/mcp` should list `stopslop` as connected too.
4. Write something. If it is clean, it goes through. If it is not, the gate tells you right away, not later, in review.

Only the gate itself (step 1's settings write, step 2, step 4) is required. The venv, the dashboard, and the MCP tools are convenience layers on top of it -- see below.

## Commands

Once you wire up the gate, it runs on its own. You do not run it by hand. `stopslop.py` covers the other actions a person does directly. Every command below takes an optional `--ruleset ID`. Leave it out, and the command resolves a ruleset the same way the live gate does: from `stopslop.config.json`, or from the built-in defaults.

- `python3 stopslop.py init` sets up the hook for your own clone, installs a git pre-commit gate (`.git/hooks/pre-commit`), and sets up the venv the MCP tools and dashboard need. Pass `--force` to replace the current settings; the pre-commit gate installs on any plain re-run and never clobbers a hook that is not stopslop's. Pass `--no-venv` to skip the venv step.
- `python3 stopslop.py precommit` gates the staged tree the way the live hook gates a write: each staged file is judged in its staged state, ratcheted against its HEAD version, so a commit is refused only for a file that is deniable and worse than it was. This is the one gate every writer shares -- an editor, a script, a session running outside this directory. Bypass once with `git commit --no-verify`.
- `python3 stopslop.py lint "some text"` checks text against the resolved ruleset. It does not write the text to any file. Use `--file PATH` to check a real file instead. Add `--all` to see every flag the engine can produce, not just the ones that will actually block a write today.
- `python3 stopslop.py scan [PATH ...]` bulk-checks an existing tree of files, no live write -- for adopting stopslop onto a codebase that already exists, not just files edited going forward. With no `--ruleset`, it resolves each file through `stopslop.config.json`, the same as a live write, and skips anything out of scope. Pass `--ruleset ID` to force every matched file through one ruleset regardless of routing (add `--glob PATTERN` to narrow which filenames get included) -- this is how to test, say, `slopwatch` against an entire existing `docs/` tree before ever adding a routing rule for it. Add `--all` for every flag per file, `--quiet` for only the summary, `--json` for machine-readable output. Exits non-zero if anything would fail a live write.
- `python3 stopslop.py terms` lists every term list a ruleset owns: its polarity, how many terms come from each layer, and the project's own registrations. Add `--list LIST_ID` to narrow it to one. Add `--add TERM --note "why"` to register a term, or `--remove TERM` to drop one. Add `--force REASON` when the ruleset's own standard already forbids the word; the reason goes on the record. This one command replaces the older `register`, `unregister`, `terms`, `glossary-packs`, and `wordlist` commands, which existed separately only because allow lists and deny lists used to be modelled as different things. Add `--new-list LIST_ID [--label LABEL] [--polarity allow|deny] [--no-additions] [--accepts-packs]` to declare a whole new custom list on `--ruleset` (not just add a term to an existing one), or `--remove-list LIST_ID` to remove its declaration (its own terms stay on disk, reappearing if re-declared).
- `python3 stopslop.py packs` lists every bulk vocabulary pack and which routing rule and term list each one currently feeds. Add `--glob GLOB --list LIST_ID --enable PACK_ID [PACK_ID ...]` to point exactly that set of packs at one list on one routing rule (drop the ids to detach them). Both `--glob` and `--list` are required to change anything: a pack carries no opinion about where it applies or what it feeds. Add `--add-pack PACK_ID --terms-file PATH [--name NAME --source SOURCE --license LICENSE --content-kind word|phrase|pattern]` to register a whole new custom pack, or `--remove-pack PACK_ID` to remove one (refused for a built-in pack).
- `python3 stopslop.py checks` lists every individually-toggleable check a ruleset has, whether it is on, its unit, and (for slopwatch and codewatch) its own threshold and action. Add `--enable CHECK_ID [CHECK_ID ...]` to turn on exactly that set (remove the ids to turn every check off). Add `--set-threshold CHECK_ID=N [...]` and/or `--set-action CHECK_ID=block|warn [...]` to tune a specific check. Add `--add-check CHECK_ID --unit sentence|document|line --catches "..." --instead "..." --fn-body-file PATH [--threshold N] [--action warn|block] [--terms-list LIST_ID]` to add a whole new custom check -- a real Python matcher, not just config -- or `--update-check CHECK_ID` (same fields) to replace an existing one's definition, or `--remove-check CHECK_ID` to remove one (refused for a built-in check).
- `python3 stopslop.py options` lists every tunable option a ruleset has that is not a per-check threshold/action (ste100's word limits and excluded vocabulary types), its current value, and its default. Add `--set KEY=VALUE [KEY=VALUE ...]` to change one or more; an option you do not mention keeps its current value.
- `python3 stopslop.py status` shows per-ruleset stats, recent gate activity, and whether the hook is even wired up yet.
- `python3 stopslop.py list-rulesets` lists every registered ruleset (tagging each `[built-in]` or `[custom]`), the glob patterns routed to it, and any custom ruleset that failed to load. Add `--add RULESET_ID [--name NAME]` to scaffold a whole new ruleset -- empty until this ruleset's own `terms`/`checks` commands fill it in, picked up in the same process, no restart -- or `--remove RULESET_ID` to remove a custom one (refused for a built-in one, or one any routing rule still routes to). **Removal deletes the ruleset's package and nothing else.** Its custom checks under `.claude/stopslop/custom_checks/<id>/`, and its `custom_term_lists`, `check_config` and `disabled_checks` entries in `stopslop.config.json`, all stay -- so re-adding the same id brings its checks and settings back, the same "removal is reversible" posture a term list already has. The cost is that a ruleset removed and never re-added leaves that data behind. Nothing purges it; delete that directory and those config keys by hand to reclaim it.
- `python3 stopslop.py --version` prints the installed version.
- `python3 stopslop.py dashboard` opens the live web dashboard. Needs the venv.


## Dashboard (optional)

`python3 stopslop.py dashboard` opens a local page at `http://localhost:8501` -- a small, bespoke FastAPI + htmx app (`src/webui/`), no build step, no external JS beyond a vendored copy of htmx itself. It shows live gate activity and per-ruleset stats, across four pages:

- `Watch` -- the live activity feed, with a callout for recent denials.
- `Checks` -- picks a ruleset and tunes every one of its checks in place: a check's on/off switch, its unit (sentence/document/line), its threshold, and its action are one editable row. It can add a whole new custom check (a real matcher function, not just a word list), optionally bound to a Vocabulary list. The "Edit" link doubles as the only place a saved custom check's matcher body is visible again -- prefilled, editable, or removable outright. A "Try it" playground lints text through the exact same gate a real write would. Each row also shows how often that check has actually fired, out of how many judged writes, and the page names any check that has never fired at all -- the number that reveals a decayed check set. It stays quiet below 25 judged writes, because a check firing on one document in ten sits out a four-write sample most of the time.
- `Vocabulary` -- searches every word in every list at once, tagged by ruleset and source, and browses or curates any single list. A built-in or pack word can't be deleted outright, only suppressed, and stays restorable. It can also declare a whole new custom list on any ruleset, edit that list's own spec afterwards (label, polarity, what it accepts -- the id stays fixed, since every word already registered is filed under it), or remove one it declared. Its own Packs section adds or removes a whole custom vocabulary pack.
- `Routing` -- the editable first-match-wins rules table, with real move-up/move-down reordering (order decides everything here), a path probe, and per-rule vocabulary-pack and check-exemption bindings. Its own Rulesets section scaffolds a whole new ruleset from just an id and a name -- empty until Checks and Vocabulary fill it in -- renames a scaffolded one in place (only the display name; the id is what every routing rule and config entry is filed under), or removes one, refused while any rule still routes to it.

Edits apply immediately and re-render straight from disk. Anything destructive confirms first, and the last change is undoable. The dashboard reads and writes the exact files the hook, the CLI, and an agent already use: `.claude/stopslop-history.log` and `stopslop.config.json`. One shared source of truth, not a second config store. A change here reaches the next gate call right away, with no session restart.

It also starts on its own the first time an MCP session loads (see `src/dashboard_launch.py`), headless, in the background -- no need to run the command by hand unless a Claude Code session was never started. Concurrent sessions loading MCP at once still produce exactly one dashboard process, not one per session: a health probe against the app's own `/health` endpoint and a file lock (`.claude/stopslop-dashboard.lock`) together guarantee only the first one to get there actually spawns it.

Uses the venv `stopslop.py init` already sets up (see Quickstart) -- nothing further to install.

## MCP tools (optional)

`src/mcp_server.py` exposes the same checks as MCP tools: `explain`, `lint_text`, `scan_codebase`, `check_word`, `list_term_lists`, `list_path_packs`, `list_checks`, `list_check_config`, `list_rulesets`, and `get_status`. `explain(file_path)` is the one to reach for first. It answers what gates that file, what would block a write there, which checks run, and which tool call resolves each kind of flag -- one call instead of guessing a ruleset and then making four more. A model can call these directly, with no Bash shell needed. Every tool takes an optional `ruleset` id, resolved the same way the CLI resolves one. A ruleset without a given capability returns a plain, structured refusal for the tools that need it, not an error. `scan_codebase` is the bulk version of `lint_text`, for the same use case as `stopslop.py scan`.

**Every one of those tools only reads.** This surface belongs to the party the gate constrains, so nothing on it can change what the gate enforces. That rule is categorical rather than case-by-case, because "does this call make the gate weaker?" has no per-call answer: adding a term to an *allow* list relaxes the gate, and adding the same term to a *deny* list tightens it. It replaces an earlier surface that could add terms, packs, checks and whole rulesets -- convenient, and a way for a model to switch off its own gate. See [SECURITY.md](SECURITY.md) for what that surface could do and why the fix was to remove the category. Growing the system is still a person's act, through `stopslop.py` or the dashboard.

This is a different kind of tool from the hook, on purpose, not a second gate. The hook sits in front of `Write` and `Edit`. It can deny a call before the write happens. The model must choose to call an MCP tool, or it never runs. A model can still write a file directly instead. No rule stops that. The MCP layer exists to cut down on denied attempts, not to replace the hook.

Uses the venv `stopslop.py init` already sets up (see Quickstart). `.mcp.json` is already in this repository, so a Claude Code session started inside it wires the server up on its own -- once the project's MCP servers are trusted (the prompt Quickstart step 2 covers). If `/mcp` does not list `stopslop` after that, run `stopslop.py status` and check its `MCP trust` line first.

`.mcp.json` is project-scoped. It only connects when Claude Code's own working directory is this repository. For a session rooted elsewhere (a separate tool that reaches this repo by absolute path, say) to see these tools too, register it at user scope instead: `claude mcp add stopslop --scope user -- python3 /absolute/path/to/stopslop/src/mcp_launch.py`.


## The evaluation harness (`src/evalab/`)

The instrument behind every number above. Each prompt runs four arms: **ungated** generates once, **gated** runs the real write-lint-revise loop, **blind** spends the gated arm's exact compute on a rewrite that is never told what was wrong, and **control** is a second ungated generation whose delta is the run's noise floor.

Three design rules keep it from flattering the tool. The gated arm is never shown a held-out check, so those measure transfer rather than instruction-following. The blind arm has matched compute, so a gain cannot be credited to the flags when a second pass would have done it. And the averages cover only prompts the loop actually revised -- including the rest does not dilute an effect, it invents one, which this harness demonstrated on itself before the scoping was fixed.

```
python3 src/evalab/run.py --live --prompt-set padding --enforce structural --workers 5
python3 src/evalab/run.py --replay evalab-runs/2026-09-01-structural/recordings \
    --prompt-set padding --enforce structural
```

`--live` costs tokens and records every call, so a run replays for free afterwards. Each run writes `result.json`, `report.txt` and all four arms' full text under `texts/`, because no metric here decides whether prose is good and the saved texts are the actual evidence.

## What it does not do

- **It is not a detector, and it is not evasion.** It removes constructions that make text read as generated. Whether that is worth wanting is your call; it makes no claim about quality.
- **It does not catch every write.** Bash detection is conservative and misses `printf` with real arguments and non-heredoc appends. `git commit --no-verify` skips the pre-commit hook.
- **`ste100` vocabulary warns and never blocks.** The dictionary holds 787 approved and 1203 forbidden words, each with a replacement, but a closed 875-word aerospace vocabulary fires constantly on software prose, so it informs a report and denies nothing.
- **`ste100` has no part-of-speech data.** The standard approves "check" as a noun and forbids it as a verb; the checker sees only the word.
- **Vocabulary auto-fix is off on purpose.** An early version substituted a word's single listed replacement without checking its part of speech and silently broke real sentences. A person caught it by hand, in this project's own README.
- **One file, one ruleset.** First match wins, except for `embedded_prose`, which sends a code file's strings and docstrings through a second prose ruleset.
- **The human control is small.** Under 12000 words across two genres, and stdlib docstrings carry no markdown, so three of the structural checks cannot fire there.

Run the whole suite with `python3 -m unittest discover -s src -p 'test_*.py'` (963 tests). See [docs/incidents/](docs/incidents/) for a real bypass of this project's own gate, and [CONTRIBUTING.md](CONTRIBUTING.md) for the one constraint this repo has that most do not: its own gate reads your contribution before a reviewer does.

## Documentation

- [How to contribute](CONTRIBUTING.md) -- how to run the tests, and the one constraint this repo has that most do not: its own gate reads your contribution before a reviewer does.
- [How to add a ruleset](docs/adding-a-ruleset.md) -- the full plugin contract: the three required functions, the three required attributes, every optional capability, and what each one adds.
- [Embedded prose](docs/embedded-prose.md) -- how one routing rule sends a code file's own strings and docstrings through a second, prose ruleset.
- [ASD-STE100 rules, extracted](docs/ASD-STE100-rules-extracted.md) -- the Part 1 rule set this project built the `ste100` ruleset against. Reference material, not this project's own prose, so the gate does not read it.
- [A gate bypass during dictionary extraction](docs/incidents/2026-08-01-ste100-dictionary-extraction-gate-bypass.md) -- an incident report on a real bypass of this project's own gate, and the fix.

## License

The code is MIT (see [LICENSE](LICENSE)). The ASD-STE100 dictionary and rule text, the three built-in vocabulary packs, and the checks ported from other projects are not: each carries its own copyright and its own terms, all stated in [NOTICE](NOTICE). Read that file before you reuse any of this content outside this project.
