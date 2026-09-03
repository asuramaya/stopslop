# stopslop

[![tests](https://github.com/asuramaya/stopslop/actions/workflows/tests.yml/badge.svg)](https://github.com/asuramaya/stopslop/actions/workflows/tests.yml)

Most anti-slop rules are wrong for your writing specifically. This is a tool for finding out which ones, and a decent starting point to begin from.

It ships a text gate that reads your prose at the moment of the write, a set of checks to start from, and an evaluation harness that measures any of it against your own writing. The harness is the unusual part. Every other tool in this category asserts that it removes AI writing tells; this one tests the claim against controls, including the free alternative to installing anything.

## Start here

If you write with a model and want the cheap 80%:

```
python3 stopslop.py rules >> CLAUDE.md
```

That is a block of named defects. Measured on 30 prompts it cut total AI-writing tells from 107 to 60, for one generation and no install.

If it matters more than that, install the gate too, and point the instruction at what the gate does *not* catch:

```
python3 stopslop.py init
python3 stopslop.py rules --complement >> CLAUDE.md
```

107 to 13, for about 2.8 generations per document.

If you want an answer about your writing rather than mine, write your prompts in a markdown file and run the harness on them:

```
python3 src/evalab/run.py --live --prompt-set my-prompts.md --compare ./my-skill.md
```

That is the actual product. Everything above is a default.

## What the evidence says

Sixteen committed runs on three models, all replayable from [`evalab-runs/`](evalab-runs/), every p-value recomputable with [`src/evalab/stats.py`](src/evalab/stats.py). One of them measured this project against the other tools in its category on the same prompts, in the same run -- as far as I can find, nobody had done that before, because until this harness there was no rig.

| tier | tells | generations |
|---|---|---|
| nothing | 107 | 1.00 |
| a skill file (any of them) | 50-60 | 1.00 |
| gate only | 30 | 2.80 |
| gate + complement skill | **13** | 2.77 |

Gate-only is dominated: It costs more than gate-plus-skill and delivers less than half as much, because an instruction front-loads the fix and the loop then needs fewer revisions. If you run the gate, run a skill beside it.

And it matters where the skill points. A block naming the checks the gate *already enforces* barely helps (26 against 30, p = 0.17). A block naming the checks it does *not* enforce reaches 13, beating the gate alone 17-2, **p = 0.0007** -- and takes held-out flags from 25 to 11, which is the first time in six rounds that number moved. A gate enforces; an instruction generalises. Pointing both at the same targets wastes the instruction.

And it holds across a document's whole life. Six documents written and then edited three times each, on three models -- 18 paired observations. The combined arm scores 8 total tells against ungated's 50 (17-0, p = 0.000015) and against the gate alone's 17 (7-0, p = 0.016), for 6.50 generations against the gate's 8.56. Cheaper and better again.

That run also killed the hypothesis it was built on. I expected documents to get sloppier as they are edited and a gate's advantage to be resisting that. Two of three models get *better* with editing; documents do not generally drift. What actually happens is that **an instruction fades**. Stated once, it works in a single turn -- roughly halving tells -- and by the fourth turn it is one voice among everything said since: pooled, instructed alone scores 33 against ungated's 50 and does not clear significance (p = 0.45). The gate is unaffected, 17 against 50, p = 0.00012, because a hook reads the text at the moment of the write however long the conversation has got. The gate's advantage over an instruction does grow with session length. The mechanism is the opposite of the one I guessed. [Findings](evalab-runs/2026-09-02-turns/FINDINGS.md).

And it holds on different weights. Re-run on a second model, the complement arm beats the gate 20 to 40 (19-3, p = 0.0009) and takes held-out flags 25 to 16 (11-2, p = 0.022). Base rates differ between models -- 88 ungated tells against 107 -- which is exactly why a check set needs measuring against the model you actually use. But the ordering of every gated arm is identical, and a blind rewrite still achieves nothing on either. [The replication](evalab-runs/2026-09-02-sonnet/FINDINGS.md) also retracts a claim the first run over-read.

Four findings that are not in this project's favour, and matter more than the win:

- The wording is not the active ingredient. stop-slop has 16.7k stars and thousands of readers' revisions. A block assembled mechanically from a check table matched it: 13-11 with 6 ties, p = 0.84. Meanwhile a blind rewrite -- told to try again, given no specifics, at three times the compute -- moved structural tells from 75 to 75. What works is naming defects, not describing quality.
- Most checks do nothing, and it matters which ones. 19 of slopwatch's 31 fired zero times across 59902 words; six carried 96% of every flag. But silence means two different things, so each check declares which it is. A *tell* is a correlate catalogued against some model at some date -- when it stops firing, it has stopped describing anything, and `decay` lists it as a prune candidate. A *defect* is wrong whatever wrote it (an emoji in body text, an em dash as an HTML entity, a generator's own scaffolding), so silence means it is rare, which is what you wanted. The last run's 22 silent checks are 18 decayed tells and 4 defects working as intended.
- Whether a check is a "tell" depends on your genre. `colon_reveal` reads 1.0x against code documentation and 25.8x against encyclopedia prose. Same check, opposite conclusion. `stopslop.py decay --against` is the command for finding out which way it falls for *your* corpus, and it wants two control genres, not one.
- The gate does not work on `ste100` at all. 433 flags against ungated's 411, p = 1.0 -- indistinguishable from doing nothing, at three generations per document. The ruleset that fires most in production is the one the loop makes no better. [Findings](evalab-runs/2026-09-02-ste100/FINDINGS.md).

And one retraction, kept because it is the most useful thing here. This project published that four checks fire more on human prose than generated prose, "across every control corpus measured". They do not -- that verdict came from a control that was mostly CPython docstrings, which carry no markdown. Against human *markdown* documentation, not one is condemned. **That is the third time a fairer corpus overturned a conclusion drawn from a narrower one.** A verdict from one corpus shape is a hypothesis.

None of this measures whether the writing is *good*. It measures whether it still reads as generated. Those are different questions and only the second is answered here.

### The caveat that bounds every number above

They come from the `padding` prompt set -- prose deliberately chosen to trip flags. On the `technical` set, real content, almost nothing tripped and the question could not be asked. These gaps are measured where the problem is worst, and for dense technical writing the whole ladder compresses, possibly to nothing. Which is the argument for measuring your own prompts rather than trusting this table.

## Tuning it to your writing

The loop the tool is built around, in four commands:

```
# 1. import rules other people already wrote and argued over
python3 stopslop.py import --vale path/to/Vale/Style --ruleset slopwatch

# 2. find out which of them discriminate for YOUR genre, not mine
python3 stopslop.py decay docs/ --against my-old-writing/ --against another-genre/

# 3. turn what survived into an instruction
python3 stopslop.py rules --complement >> CLAUDE.md

# 4. measure it against your own writing tasks
python3 src/evalab/run.py --live --prompt-set my-prompts.md --compare ./my-skill.md
```

Step 1 works: [vale-ai-tells](https://github.com/krishnasunkam/vale-ai-tells) imports 17 of 17 rules, and the [Microsoft Writing Style Guide](https://github.com/vale-cli/Microsoft) 42 of its 44 actual rules. There is a whole ecosystem of these at [vale.sh/explorer](https://vale.sh/explorer) -- Microsoft, Google, Elastic, write-good, proselint, alex.

Step 2 is the one nothing else in this category can do, and step 4 is what makes the answer yours instead of mine.

## What it actually does

A `PreToolUse` hook. Before Claude Code writes or edits a file, the hook gets the text, resolves the path to a ruleset through `stopslop.config.json` (first glob match wins), lints it, and either passes it, auto-fixes mechanical problems, or denies the write with the list of what to fix. A `pre-commit` hook gates the staged tree, ratcheted against HEAD.

It is not a security boundary and does not see every write path. [SECURITY.md](SECURITY.md) is specific about what it misses.

## Rulesets

A ruleset is a small Python package under `src/rulesets/` supplying three functions (`lint_and_gate`, `blocking_semantic_flags`, `apply_mechanical_fixes`) and three attributes. The gate knows nothing else about it. See [docs/adding-a-ruleset.md](docs/adding-a-ruleset.md) for the contract.

- `slopwatch` -- the default for prose, 31 checks. AI writing tells: wording habits, and the formatting habits that outlast them. Every check warns; none blocks.
- `codewatch` -- `.py` files, 10 checks. Debris that accumulates as code is EDITED: leftover `print()` calls, TODO stubs, comments narrating a refactor, a bare `except: pass`. Blocks that last one, because it is a defect rather than a tell. It was documented as "the tells an agent leaves in source" until it was measured, and that was wrong -- across six modules each edited three times, opus produced one flag in 16089 words and haiku six in 6406. Machine-written Python does not carry this fingerprint, and the rate tracks model capability rather than authorship. Reach for it when code is being changed over a long session, not when it is being generated. [Findings](evalab-runs/2026-09-03-codewatch/FINDINGS.md).
- `ste100` -- ASD-STE100 Simplified Technical English, 13 checks, 12 of them blocking. Opt-in: it reaches no file until a rule names it. It is a controlled language for maintenance procedures, and it buys precision with a deliberate monotone. Right for a runbook, a category error for a README -- this tool proved that on itself, flagging 23 sentences of `SECURITY.md` over the words "blocking", "warning" and "reading".

Defaults with no config file: `slopwatch` on `.md`/`.txt`/`.rst`, `codewatch` on `.py`, `.claude/` out of scope. Route procedures to `ste100` by name, above the general rule. This repository routes exactly one file that way.

The block/warn split follows one rule: a check blocks when it catches a *defect*, and warns when it catches a *tell*. That is now declared per check as `Check.kind` rather than described here, and a test holds that anything which blocks a write is a defect -- denying a write on evidence that is only a correlate is the unsound-gate criticism this project accepted. A tell is a correlate, and text that dodges all 31 checks and says nothing still passes.

## Quickstart

1. Clone the repository, then run `python3 stopslop.py init`. This writes `.claude/settings.local.json` for your own clone location, installs a git pre-commit gate, and sets up the virtual environment the optional MCP tools and dashboard need (`python3 -m venv .venv`, then `pip install -r requirements.txt`) -- no manual edit needed for any of it. Pass `--no-venv` to skip that last, optional part.
2. Start (or restart) a Claude Code session inside the repository. The first time, Claude Code asks whether to allow this project's MCP servers (`.mcp.json`) -- say yes. Miss this and the MCP tools, and the dashboard they auto-start, silently never connect; nothing else in this setup depends on it. The `SessionStart` hook also reports any integrity problem, and memory context from prior gate activity, for every ruleset with any.
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
- `python3 stopslop.py list-rulesets` lists every registered ruleset (tagging each `[built-in]` or `[custom]`), the glob patterns routed to it, and any custom ruleset that failed to load. Add `--add RULESET_ID [--name NAME]` to scaffold a whole new ruleset -- empty until this ruleset's own `terms`/`checks` commands fill it in, picked up in the same process, no restart -- or `--remove RULESET_ID` to remove a custom one (refused for a built-in one, or one any routing rule still routes to). Removal deletes the ruleset's package and nothing else. Its custom checks under `.claude/stopslop/custom_checks/<id>/`, and its `custom_term_lists`, `check_config` and `disabled_checks` entries in `stopslop.config.json`, all stay -- so re-adding the same id brings its checks and settings back, the same "removal is reversible" posture a term list already has. The cost is that a ruleset removed and never re-added leaves that data behind. Nothing purges it; delete that directory and those config keys by hand to reclaim it.
- `python3 stopslop.py rules` prints the ruleset's enabled checks as a block of writing instructions. Add `--complement` if you also run the gate -- it prints only the checks the gate will not deny on, which measured 13 total tells against 30 for the gate alone, and is the only thing that has ever moved the held-out number, ready to paste into `CLAUDE.md`. This is the free alternative to installing the gate, and this project's own evaluation says it is worth about half of it -- see What the evidence says. Only enabled checks are printed, since an instruction naming a check you switched off asks for something nothing here enforces, and the block stamps in its own regeneration command because a pasted block outlives the memory of where it came from. Add `--quiet` for just the block.
- `python3 stopslop.py decay [PATHS]` measures every check in a ruleset against a real corpus and reports hits, files, rate per 1000 words and share of all flags -- including the zeros, then names the silent ones. A check that never fires produces no output, which is exactly why a decayed check set is invisible.
  - `--against PATH` adds a control corpus of prose you want to sound *like*, and reports which checks fire more on the measured text than on it: the only evidence that a check detects a machine rather than a style. Repeat it for a second genre. One corpus nearly cost this project a good check -- `colon_reveal` reads 1.0x against code documentation and 25.8x against pre-2022 encyclopedia prose, because code docs are full of colons whatever wrote them. A verdict needs every control to agree; controls that disagree give `disputed`, which is the genres disagreeing rather than a weak result.
  - `--calibrate` reports where each check's band sits and which way the gate misses it. Point `--against` at your own writing and it calibrates to your voice, which a static skill file cannot do. It reports the gap, never a threshold number: a threshold's meaning is per-check and the contract does not carry it.
  - `python3 -m evalab.human_corpus [DIR]` builds a control from CPython stdlib docstrings and package docs; `--wikipedia` builds a non-code one from article revisions dated before 2022. Neither corpus is committed -- the builder and a manifest are, so a rebuilt corpus can be shown to be the one a number came from without redistributing it.
- `python3 stopslop.py import --vale DIR` imports a Vale style package as real custom checks on a ruleset -- `existence` rules and `substitution` swap maps, the two shapes that carry almost every rule in the wild. Verified against real packages: [vale-ai-tells](https://github.com/krishnasunkam/vale-ai-tells) imports 17 of 17, and the [Microsoft Writing Style Guide](https://github.com/vale-cli/Microsoft) 42 of its 44 actual rules (the other 15 files in that repository are Vale config, not rules; the 2 real failures use Go look-behinds Python's `re` cannot compile). A rule outside the supported subset is refused by name, never approximated, and refusals print beside the imports -- a partial import that hides its gaps is how someone comes to believe they are covered. Add `--dry-run` to see what would land.
  There is a whole ecosystem of these at [vale.sh/explorer](https://vale.sh/explorer): Microsoft, Google, Elastic, write-good, proselint, alex. This is what the pluggable-ruleset architecture is for -- the rules other people have already written, rather than more of mine.
- `python3 stopslop.py --version` prints the installed version.
- `python3 stopslop.py dashboard` opens the live web dashboard. Needs the venv.


## Dashboard (optional)

`python3 stopslop.py dashboard` opens a local page at `http://localhost:8501` -- a small FastAPI + htmx app (`src/webui/`), no build step, no external JS beyond a vendored copy of htmx.

[![The Checks page](docs/screenshots/checks.png)](docs/dashboard.md)

Four pages: Watch (what the gate has actually done), Checks (which rules exist and how often each one fires), Vocabulary (the word lists behind the checks, and the packs that fill them), Routing (which ruleset judges which file, first match wins).

[docs/dashboard.md](docs/dashboard.md) explains each page -- what to look for, what the columns mean, and for every page the CLI command that answers the same question without a browser. It is written for a person looking at the screen and for a model reading the file; an agent should generally use the commands, since every page reads the same two files the CLI does.

Edits apply immediately and re-render from disk. Anything destructive confirms first, and the last change is undoable. It reads and writes exactly what the hook, the CLI and an agent already use -- `.claude/stopslop-history.log` and `stopslop.config.json`. One source of truth, and a change reaches the next gate call with no session restart.

It also starts on its own the first time an MCP session loads (`src/dashboard_launch.py`), headless, in the background. Concurrent sessions still produce exactly one process: a health probe against `/health` plus a file lock (`.claude/stopslop-dashboard.lock`) guarantee only the first one to get there spawns it.

Uses the venv `stopslop.py init` already sets up -- nothing further to install.

## MCP tools (optional)

`src/mcp_server.py` exposes the same checks as MCP tools: `explain`, `lint_text`, `scan_codebase`, `check_word`, `list_term_lists`, `list_path_packs`, `list_checks`, `list_check_config`, `list_rulesets`, and `get_status`. `explain(file_path)` is the one to reach for first. It answers what gates that file, what would block a write there, which checks run, and which tool call resolves each kind of flag -- one call instead of guessing a ruleset and then making four more. A model can call these directly, with no Bash shell needed. Every tool takes an optional `ruleset` id, resolved the same way the CLI resolves one. A ruleset without a given capability returns a plain, structured refusal for the tools that need it, not an error. `scan_codebase` is the bulk version of `lint_text`, for the same use case as `stopslop.py scan`.

Every one of those tools only reads. This surface belongs to the party the gate constrains, so nothing on it can change what the gate enforces. That rule is categorical rather than case-by-case, because "does this call make the gate weaker?" has no per-call answer: adding a term to an *allow* list relaxes the gate, and adding the same term to a *deny* list tightens it. It replaces an earlier surface that could add terms, packs, checks and whole rulesets -- convenient, and a way for a model to switch off its own gate. See [SECURITY.md](SECURITY.md) for what that surface could do and why the fix was to remove the category. Growing the system is still a person's act, through `stopslop.py` or the dashboard.

This is a different kind of tool from the hook, on purpose, not a second gate. The hook sits in front of `Write` and `Edit`. It can deny a call before the write happens. The model must choose to call an MCP tool, or it never runs. A model can still write a file directly instead. No rule stops that. The MCP layer exists to cut down on denied attempts, not to replace the hook.

Uses the venv `stopslop.py init` already sets up (see Quickstart). `.mcp.json` is already in this repository, so a Claude Code session started inside it wires the server up on its own -- once the project's MCP servers are trusted (the prompt Quickstart step 2 covers). If `/mcp` does not list `stopslop` after that, run `stopslop.py status` and check its `MCP trust` line first.

`.mcp.json` is project-scoped. It only connects when Claude Code's own working directory is this repository. For a session rooted elsewhere (a separate tool that reaches this repo by absolute path, say) to see these tools too, register it at user scope instead: `claude mcp add stopslop --scope user -- python3 /absolute/path/to/stopslop/src/mcp_launch.py`.


## The evaluation harness (`src/evalab/`)

The instrument behind every number above. Each prompt runs five arms, plus one more for every competing tool named with `--compare`:

- ungated generates once. The baseline.
- control is a second ungated generation. Its delta is the run's noise floor, and a gate delta smaller than it is not a finding whatever direction it points.
- blind spends the gated arm's exact compute on a rewrite that is never told what was wrong. Whatever it gains is what a second pass gains.
- instructed pastes the enforced checks' own wording into the prompt and generates once. This is the free alternative to installing anything, and the gate has to beat it to be worth the install.
- `--compare NAME` runs another project's skill file as its own arm, in full, from [`src/evalab/interventions/`](src/evalab/interventions/). Each is vendored beside its upstream MIT license; a test fails if one appears without one.
- gated runs the real write-lint-revise loop against the live ruleset.

Four design rules keep it from flattering the tool. The gated arm is never shown a held-out check, so those measure transfer rather than instruction-following -- and neither is the instructed arm, which a test enforces. The blind arm has matched compute, so a gain cannot be credited to the flags when a second pass would have done it. The instructed arm's text is built from the ruleset's own check metadata rather than hand-written, so it cannot be quietly weakened relative to what the gate enforces, and a ruleset gaining a check gains it in both arms at once. And the averages cover only prompts the loop actually revised -- including the rest does not dilute an effect, it invents one, which this harness demonstrated on itself before the scoping was fixed.

```
python3 src/evalab/run.py --live --prompt-set padding --enforce structural --workers 5
python3 src/evalab/run.py --replay evalab-runs/2026-09-01-instructed/recordings \
    --prompt-set padding --enforce structural
python3 src/evalab/stats.py evalab-runs/2026-09-01-instructed/result.json gated instructed
```

`--live` costs tokens and records every call, so a run replays for free afterwards. A live run is a couple of hundred subprocesses over half an hour and one of them will eventually fail for no reason: `--resume DIR` replays what a recordings directory already holds and generates only what it does not, which is how the run above was finished after `claude` exited 1 at call 258 of 264. Resume is safe for the same reason replay is -- a recording is keyed by the exact message list plus how many times that list has been asked, so a resumed call either matches its own question or misses and is regenerated.

`stats.py` pairs any two arms of a saved `result.json` by prompt: an exact two-sided sign test with ties dropped, and a seeded percentile bootstrap on the mean paired difference. Every p-value in this README is reproducible with it, and a test holds the published structural claim against its own saved run so a future change to the harness fails the suite rather than silently rewriting history.

Each run writes `result.json`, `report.txt`, the recordings, and the ungated, instructed and gated texts under `texts/`, because no metric here decides whether prose is good and the saved texts are the actual evidence. The sixteen committed runs are in [`evalab-runs/`](evalab-runs/), each with its own `FINDINGS.md`.

## What it does not do

- It is not a detector, and it is not evasion. It removes constructions that make text read as generated. Whether that is worth wanting is your call; it makes no claim about quality.
- It does not catch every write. Bash detection is conservative and misses `printf` with real arguments and non-heredoc appends. `git commit --no-verify` skips the pre-commit hook.
- `ste100` vocabulary warns and never blocks. The dictionary holds 787 approved and 1203 forbidden words, each with a replacement, but a closed 875-word aerospace vocabulary fires constantly on software prose, so it informs a report and denies nothing.
- `ste100` has no part-of-speech data. The standard approves "check" as a noun and forbids it as a verb; the checker sees only the word.
- Vocabulary auto-fix is off on purpose. An early version substituted a word's single listed replacement without checking its part of speech and silently broke real sentences. A person caught it by hand, in this project's own README.
- One file, one ruleset. First match wins, except for `embedded_prose`, which sends a code file's strings and docstrings through a second prose ruleset.
- The human control is small. Under 12000 words across two genres, and stdlib docstrings carry no markdown, so three of the structural checks cannot fire there.

Run the whole suite with `python3 -m unittest discover -s src -p 'test_*.py'` (1157 tests). See [docs/incidents/](docs/incidents/) for a real bypass of this project's own gate, and [CONTRIBUTING.md](CONTRIBUTING.md) for the one constraint this repo has that most do not: its own gate reads your contribution before a reviewer does.

## Documentation

- [How to contribute](CONTRIBUTING.md) -- how to run the tests, and the one constraint this repo has that most do not: its own gate reads your contribution before a reviewer does.
- [What this project's own documentation scores](docs/self-audit.md) -- the tool run on its own prose, then re-run after acting on it. 3.32 structural tells per 1000 words against human documentation's 3.18 and ungated generation's 13.32. The first pass found this README using bold as a label at 2.6x the human rate, and found a false positive in the check itself.
- [Reading the dashboard](docs/dashboard.md) -- what each of the four pages shows, what to look for, and the CLI command that answers the same question without a browser. Written for humans and for models.
- [How to add a ruleset](docs/adding-a-ruleset.md) -- the full plugin contract: the three required functions, the three required attributes, every optional capability, and what each one adds.
- [Embedded prose](docs/embedded-prose.md) -- how one routing rule sends a code file's own strings and docstrings through a second, prose ruleset.
- [ASD-STE100 rules, extracted](docs/ASD-STE100-rules-extracted.md) -- the Part 1 rule set this project built the `ste100` ruleset against. Reference material, not this project's own prose, so the gate does not read it.
- [The evaluation runs](evalab-runs/) -- all sixteen, in the order they were run, with what each one asked and what it found. The conclusions change between them.
- [A gate bypass during dictionary extraction](docs/incidents/2026-08-01-ste100-dictionary-extraction-gate-bypass.md) -- an incident report on a real bypass of this project's own gate, and the fix.

## License

The code is MIT (see [LICENSE](LICENSE)). The ASD-STE100 dictionary and rule text, the three built-in vocabulary packs, and the checks ported from other projects are not: each carries its own copyright and its own terms, all stated in [NOTICE](NOTICE). Read that file before you reuse any of this content outside this project.
