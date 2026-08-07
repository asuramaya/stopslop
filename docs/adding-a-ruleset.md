# How to add a ruleset

This document is for anyone who wants to add a fourth ruleset to stopslop.
`ste100`, `slopwatch`, and `codewatch` are the three reference examples.
Read `src/rulesets/codewatch/` first. It is the smallest of the three.

## What a ruleset is

A ruleset is a Python package at `src/rulesets/<id>/`. Its
`__init__.py` exposes a small, fixed set of names. Nothing outside that
package knows anything about the rules or the vocabulary inside it. Not the
hook, the CLI, the MCP server, `core/`, or another ruleset. Those callers
only ever call the names below.

## The required names

Every `__init__.py` under `src/rulesets/` must define these six names,
or `rulesets._register()` refuses it at import time:

```python
RULESET_ID = "your_id"       # stable, used in config files, the CLI, and log data
RULESET_NAME = "Your Name"   # shown in CLI output and deny messages
CAPABILITIES = frozenset()   # see Capabilities below; empty is valid

def lint_and_gate(text, *, context=None, file_path=None): ...
def blocking_semantic_flags(semantic_flags): ...
def apply_mechanical_fixes(text, file_path=None): ...
```

`file_path` is part of the contract, not an optimisation. Vocabulary packs
attach to the routing rule that matched a file. Two files that go to the
same ruleset can therefore have different vocabularies. Your ruleset is
free to ignore the argument. A ruleset that cannot ACCEPT it breaks the
live gate.

`lint_and_gate` returns a dict with four keys: `status`, `sentence_count`,
`mechanical_violations`, and `semantic_flags`. The last two are lists of
flags. A flag looks like this:

```python
{"kind": "your_check_name", "label": "the specific word or phrase, or None",
 "detail": {...your own shape...}, "text": "the sentence, or None"}
```

`kind` groups flags for two things: the per-ruleset memory summary, and
`core.flags.dedup_flags`. `label` is what `dedup_flags` collapses repeat
occurrences on. Leave it `None` for a check with no meaningful
per-occurrence identity narrower than the whole document. An em-dash count
is one example. `core.flags.default_label(detail)` covers the common case:
it picks `detail["word"]`, `detail["phrase"]`, or `detail["modal"]`, in
that order.

## Mechanical vs semantic

If a safe, deterministic rewrite exists, the flag goes in
`mechanical_violations`. `apply_mechanical_fixes` performs the rewrite.
Everything else goes in `semantic_flags` -- text that needs a human or a
model to decide, never a blind rewrite. This split is not specific to
ASD-STE100. `slopwatch` proves it: `stock_adverb` is a real mechanical
check with no vocabulary tiers or dictionary behind it at all.

`blocking_semantic_flags(semantic_flags)` decides which of those flags
actually deny a write. This is YOUR ruleset's own policy, not a shared
mechanism. `ste100` excludes a fixed list of vocabulary flag types.
`slopwatch` uses a count threshold instead. Pick whatever policy fits the
problem your ruleset targets. The gate itself never inspects a flag's
content to decide this. It only calls your function.

## Optional names

Add these names only for a ruleset that needs them:

- `TRACKED_FILES = ["lint.py", ...]` -- file names, relative to your
  package directory, for `integrity_check.py` to hash and watch for drift.
- `CHECKS = {"kind": (catches, instead), ...}` -- two facts per check: what
  it catches, and what to do instead. A `kind` with no entry still shows up
  everywhere, with generic text.
- `DENY_POLICY = {"text": ..., "blocks_alone_at": {...}}` -- what actually
  denies a write, in your own words. `blocks_alone_at` is legacy. Declare
  the key as `{}` on every ruleset. ste100 always does. A ruleset with the
  newer `"check_config"` capability declares it too. See that capability's
  own entry below for the shape that replaced a hardcoded, ruleset-wide
  `blocks_alone_at` dict. The new shape is a real, project-editable
  per-check setting. slopwatch and codewatch both moved to it. A fourth
  ruleset can go straight to `"check_config"`.

  format() fills the `text` with your live option values, where it names
  any. A `"check_config"` ruleset's text is usually plain prose instead.
  There is no longer one shared number to fill in.

  Tests check this against what `blocking_semantic_flags` actually does.
  A policy sentence that nothing verifies still carries the authority of
  one that does. That makes it worse than no sentence at all. See
  `src/test_check_text.py`.
- `CHECK_OPTIONS = {"check_id": ("option_name", ...)}` -- for a ruleset
  with the older `"options"` capability (ste100): which tunable option
  belongs to which check. Declare it. Never let a caller infer the link
  from a shared name prefix. A `"check_config"` ruleset needs none of
  this. Every check gets the same `{threshold, action}` pair. There is no
  per-check option-ownership map to declare.
- `stats()` -- a dict of short strings. `stopslop.py status` and the
  `get_status` MCP tool show these under your ruleset's own name.

Write the two `CHECKS` fields as bare facts. Do not join them into one
sentence. Do not write either one in the voice of a single screen. Each
consumer writes its own prose from them. The dashboard's Checks table
describes a control. The per-ruleset memory primer
(`generate_coaching_memory.py`) reports a repeat offence, with a real count
in front of it.

These two fields once were a single prewritten sentence, in the primer's
voice, because the primer was then the only consumer. The dashboard later
reused those same strings under a "what it catches" column header. Then 37 of 43
checks showed one sentence template, once per row, down a whole column.
If that returns, `src/test_check_text.py` fails the build.

## Capabilities

Each entry in `CAPABILITIES` obligates a set of extra names.
`rulesets._register()` enforces this at import time -- see
`CAPABILITY_ATTRS` in `src/rulesets/__init__.py`. Declare only what you
implement. A ruleset stubs out nothing. Every caller reads `CAPABILITIES`
first, so a missing capability gives a clean refusal, not an error.

**`"terms"`** -- your ruleset has word lists a project can extend. Declare
`TERM_LISTS` (see `rulesets/codewatch/lint.py` for the smallest example)
and define:

```python
def list_term_lists(file_path=None): ...
def add_term(list_id, term, note="", force=False): ...
def remove_term(list_id, term): ...
```

Delegate all three to `core/terms.py`. That module owns the layered
`built_in -> packs -> project` resolution. It also owns the tombstone
subtraction that lets a project remove a shipped word.

Each list declares what it holds and what may be done to it:

- `built_ins`, the words your ruleset ships for this list. Pass a dict to
  give each entry metadata, or any iterable of strings for bare words.
- `accepts_packs`, default false. Set it true to let a project feed this
  list from a shared vocabulary pack.

- `polarity`, `"allow"` or `"deny"`. That one field is the whole difference
  between two capabilities this project used to have: `"glossary"` (ste100)
  and `"wordlists"` (slopwatch, codewatch). They were never two concepts.
- `feeds`, the check this list supplies. Declare it. Do not depend on a
  shared id between the list and the check. ste100 maps three lists onto
  one check. A UI that paired them by name showed that check with no
  words at all.
- `content_kind`, one of `word`, `phrase`, `pattern`. A pack declares the
  same fact about itself. If your list cannot read a pack's kind, the bind
  fails where it happens. This keeps a bag of nouns out of a list of
  regular expressions.
- `accepts_additions`, default true. For shipped reference data a project
  must not add to, set it false. Removal and restore stay open. A closed
  list is not a frozen list.

**`"word_lookup"`** -- define `check_word(word)`. It returns a dict with at
least a `"status"` key. Declare this capability only for a ruleset with a
real external standard behind it, to look one word up against. See
`rulesets/ste100/__init__.py`.

**`"checks"`** -- a project can turn each of your checks off on its own:

```python
def list_checks(): ...                      # {id: {catches, instead, enabled}}
def set_enabled_checks(check_ids): ...      # REPLACE: these and only these
def set_checks_enabled(states): ...         # MERGE: {id: bool}, leave the rest
```

Define both write shapes. The difference is not cosmetic. A caller with the
full picture means replace. `stopslop.py checks --enable a b c` is one. A
caller with only a PARTIAL view means merge. A filtered table is one, and
so is a single toggle. If a ruleset offers the replace form alone, a
partial caller eventually saves its partial list as a whole one. The
dashboard did exactly that. It saved a search-filtered table, and it turned
off 18 of slopwatch's 20 checks, with a success message. Delegate to
`core.config.save_disabled_checks` and `core.config.merge_disabled_checks`.

**`"options"`** -- your ruleset has tunable numeric thresholds that are not
per-check (or belong to a `CHECK_OPTIONS`-declared check, ste100's shape).
Define `list_options()` and `set_options(options)`. `set_options` merges.

**`"check_config"`** -- every check gets its own `{threshold, action}`. This
replaces one shared, ruleset-wide density number. slopwatch and codewatch
both use it. See either's `lint.py` for `DEFAULT_CHECK_CONFIG` and
`_check_config()`. See `core.config.check_config` and `save_check_config`
for the storage. `threshold` is the occurrence count a check needs before
it counts as triggered. `core.flags.flag_weight` weighs those occurrences.
It does not use the deduped count. `action` is `"block"` or `"warn"`. A
`"block"` check denies the write on its own, once triggered. A `"warn"`
check only shows. It never denies a write by itself. Define:

```python
def list_check_config(): ...                      # {id: {threshold, action, default_threshold, default_action}}
def set_check_config(check_id, threshold=None, action=None): ...   # merge: only the fields passed change
```

`blocking_semantic_flags` groups the raw flags by check id. It compares
each group's weight against that check's own threshold. A group returns
only if the check triggered, and its action is `"block"`. There is no
ruleset-wide aggregate left to sum across different checks. A document can
carry any number of triggered `"warn"` checks, and it still passes. Give
every check in `ALL_CHECK_IDS` an entry in `DEFAULT_CHECK_CONFIG`.
`src/test_check_text.py`'s `DenyPolicyMatchesBehaviourTests` fails the
build on a missing one.

## How to register it

Add two lines to `src/rulesets/__init__.py`:

```python
from rulesets import your_id as _your_id
_register(_your_id)
```

Registration is explicit and manual on purpose, not a directory scan. What
rulesets exist stays a single fact, visible in one diff.

## Routing files to it

Nothing routes to a new ruleset until `stopslop.config.json` names it. Add
a rule:

```json
{"glob": "some/path/*.md", "ruleset": "your_id"}
```

Rules check in order. The first match wins. A rule with `"ruleset": null`
takes a path out of scope entirely, the way `.claude/*` already is by
default. See `stopslop.config.json.example` for the full default set.

## How to test it

Give your ruleset its own `src/rulesets/<id>/test_lint.py`, in plain
stdlib `unittest`. Use one class per check, one class for your deny
policy, and one for `lint_and_gate` integration. Run `python3 -m unittest
discover -s src -p 'test_*.py'` from the repository root. This
command picks up every ruleset's suite together.
