# How to add a ruleset

This document is for anyone who wants to add a fourth ruleset to stopslop.
`ste100`, `slopwatch`, and `codewatch` are the three reference examples.
Read `src/rulesets/codewatch/` first. It is small, and it has no glossary,
so it shows the minimum real ruleset.

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
CAPABILITIES = frozenset()   # a subset of {"glossary", "word_lookup"}; empty is valid

def lint_and_gate(text, *, context=None): ...
def blocking_semantic_flags(semantic_flags): ...
def apply_mechanical_fixes(text): ...
```

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
- `PRINCIPLE_TEXT = {"kind": "reminder prose", ...}` -- feeds the
  per-ruleset memory summary (`generate_coaching_memory.py`). A `kind` with
  no entry here still shows up, with a generic sentence.
- `stats()` -- a dict of short strings. `stopslop.py status` and the
  `get_status` MCP tool show these under your ruleset's own name.

## Capabilities

If your ruleset also defines these three functions, declare `"glossary"`:

```python
def register_term(word, note="", override_unapproved=None): ...
def unregister_term(word): ...
def list_terms(): ...
```

Each returns `{"ok": bool, "status": str, "message": str}`. See
`rulesets/ste100/glossary.py` for the reference shape. It also shows the
override-a-real-rule path.

If your ruleset also defines `check_word(word)`, declare `"word_lookup"`.
`check_word` returns a dict with at least a `"status"` key. See
`rulesets/ste100/__init__.py`'s `check_word` for the reference shape. It
also shows how the function handles a word class its own vocabulary
checker deliberately skips: modals.

A ruleset with neither capability, like `slopwatch`, defines none of these
six functions. Nothing stubs them out. The CLI and the MCP server check
`ruleset.CAPABILITIES` before they call either group. If a ruleset lacks
the capability, both return a clean refusal instead of an error.

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
