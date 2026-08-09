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
actually deny a write. This is YOUR ruleset's own function, not a shared
mechanism. All three shipped rulesets implement it the same way: each
check's own `{threshold, action}` decides, per check -- see the
`"check_config"` capability below. The gate itself never inspects a
flag's content to decide this. It only calls your function.

## Optional names

Add these names only for a ruleset that needs them:

- `TRACKED_FILES = ["lint.py", ...]` -- file names, relative to your
  package directory, for `integrity_check.py` to hash and watch for drift.
- `CHECKS_TABLE = lint.CHECKS_TABLE` -- see "checks" below. Re-export it
  from `__init__.py` the same way `TERM_LISTS` already is. A check with no
  entry still shows up everywhere, with generic text.
- `stats()` -- a dict of short strings. `stopslop.py status` and the
  `get_status` MCP tool show these under your ruleset's own name.

There is no separate deny-policy declaration. Each check's own `action`
field is the whole policy -- see `"check_config"` below. Two older
declarations are gone: a prose policy sentence with format() slots, and
a check-to-option map for a ruleset-wide options dict. Only ste100 ever
carried either one.

Write a `Check`'s `catches` and `instead` as bare facts. Do not join them
into one sentence. Do not write either one in the voice of a single
screen. Each consumer writes its own prose from them. The dashboard's
Checks table describes a control. The per-ruleset memory primer
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

Each list declares what it holds and what can be done to it:

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

**`"checks"` and `"check_config"`** -- declare one `CheckTable` in your
`lint.py`, not a hand-built version of either capability's own machinery.
The shared engine lives in `src/core/checks.py`. See
`src/rulesets/codewatch/lint.py` for the smallest real example.

```python
from core import checks as _checks

CHECKS_TABLE = {
    "your_check": _checks.Check(
        id="your_check", unit=_checks.Unit.SENTENCE, fn=check_your_check,
        catches="What this check catches, in plain words",
        instead="What to do about it instead",
        default_threshold=1, default_action="warn"),   # "warn" is the safe default; "block" denies alone once triggered
    ...
}
```

`unit` names the granularity your check's own function actually reads:

- `SENTENCE` -- one sentence at a time (most checks)
- `SENTENCES` -- the whole list, for a cross-sentence check
- `LINE` -- one line at a time
- `LINE_LOOKAHEAD` -- a line, plus the next one
- `LINES_INDEXED` -- the whole file, plus an index
- `DOCUMENT` -- the whole assembled text, once per call

This is documentation today. A shared run loop does not read it yet.
Your own `lint_and_gate` still calls `fn` directly, in whatever order and
shape it needs.

The `terms_list` field names the `TERM_LISTS` key this check reads from
-- see "terms" below. Not every check has one. A check with no
vocabulary binding omits it.

Set `dedup=False` on a check with no meaningful per-occurrence identity.
An em-dash count is one example. This is the same case
`core.flags.dedup_flags`'s `exclude_kinds` already covers.

Every `__init__.py` method both capabilities obligate is then a one-line
delegation:

```python
def list_checks():
    return _checks.list_checks(lint.CHECKS_TABLE, paths.find_project_root(__file__), RULESET_ID)
def set_enabled_checks(check_ids):
    _checks.set_enabled_checks(lint.CHECKS_TABLE, paths.find_project_root(__file__), RULESET_ID, check_ids)
def set_checks_enabled(states):
    _checks.set_checks_enabled(lint.CHECKS_TABLE, paths.find_project_root(__file__), RULESET_ID, states)
def list_check_config():
    return _checks.list_check_config(lint.CHECKS_TABLE, paths.find_project_root(__file__), RULESET_ID)
def set_check_config(check_id, threshold=None, action=None, **params):
    _checks.set_check_config(lint.CHECKS_TABLE, paths.find_project_root(__file__), RULESET_ID,
                              check_id, threshold=threshold, action=action, **params)
```

`set_enabled_checks` is REPLACE (these and only these). `set_checks_enabled`
is MERGE (`{id: bool}`, leave the rest). Define both -- the difference is
not cosmetic. A caller with the full picture means replace.
`stopslop.py checks --enable a b c` is one. A caller with only a PARTIAL
view means merge. A filtered table is one, and so is a single toggle. If a
ruleset offers the replace form alone, a partial caller eventually saves
its partial list as a whole one. The dashboard did exactly that once. It
saved a search-filtered table, and it turned off 18 of slopwatch's 20
checks, with a success message.

`threshold` is the occurrence count a check needs before it counts as
triggered. `core.flags.flag_weight` weighs those occurrences. It does not
use the deduped count. `action` is `"block"` or `"warn"`. A `"block"`
check denies the write on its own, once triggered. A `"warn"` check only
shows. It never denies a write by itself.

`blocking_semantic_flags` groups the raw flags by check id. It compares
each group's weight against that check's own threshold, and returns only
the groups of a triggered `"block"` check. There is no ruleset-wide
aggregate to sum across different checks. A document can carry any
number of triggered `"warn"` checks and still pass:

```python
def blocking_semantic_flags(semantic_flags):
    project_root = _paths.find_project_root(__file__)
    return _checks.blocking_semantic_flags(CHECKS_TABLE, project_root, "your_id", semantic_flags)
```

A check with extra numbers of its own declares a `params` dict on its
`Check` entry -- `{"name": default_int, ...}`.

The `length` check in ste100 carries its two word limits this way.

`list_check_config` reports them under a `"params"` key on that check:
`{name: {"value": N, "default": N}}`.

`set_check_config` takes them as keyword arguments. It refuses an
unknown name for that check. A parameter belongs to its check. No
ruleset-wide options dict exists for it to land in, and no shared table
column carries it.

## How to register it

Nothing to add. `src/rulesets/__init__.py` scans its own subpackages at
import time (`_discover_and_register`). It registers any that declares
`RULESET_ID` -- a new package under `src/rulesets/<your_id>/` is enough.
It silently skips a subpackage with no `RULESET_ID`, as a non-ruleset
helper. One that declares `RULESET_ID` but fails the required-names
contract still raises `InvalidRulesetError` at import time, loudly, the
same as a hand-registered ruleset always has.

This traded away a previously deliberate choice. A hardcoded import list
kept "what rulesets exist" a single fact, visible in one diff.

The safeguard against that loss is a test in `core/test_config.py`. It
checks the real registry against today's known set. An accidental new
ruleset -- a stray directory, an experiment left half-done -- still
fails the build. It fails at test time now, not just at a glance over
`rulesets/__init__.py`.

When you add a real fourth ruleset, update that test's expected set.

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
