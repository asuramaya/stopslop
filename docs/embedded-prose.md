# Embedded prose: a second ruleset for the strings inside code

A routing rule can name a prose ruleset for the code files it matches:

```json
{"glob": "*.py", "ruleset": "codewatch", "embedded_prose": "slopwatch"}
```

The gate then runs both. The host ruleset judges the whole file exactly
as before. The named prose ruleset judges the string literals and
docstrings that `core/extract.py` pulls out. Either gate denying denies
the write.

## Why this exists

The routing model had a crack exactly where this project's own UI copy
lived. `configure.py` routes to codewatch, which judges comments but
never string literals. ste100 and slopwatch judge prose, but only whole
`.md`/`.txt`/`.rst` files. The dashboard's captions -- the most
user-facing text in the product -- reached no ruleset at all. A gate
named stopslop shipped screens of prose it could never lint, and the
proof was empirical: several sessions of manual UI-copy review kept
finding, by eye, exactly the repetition and register drift a prose
ruleset flags mechanically.

The original pluggable-ruleset plan deferred this as "per-block-type
ruleset mixing within one file", with the note that it was a real
feature with real complexity and no current need. The need arrived. The
feature that shipped is deliberately smaller than the deferred one: one
extra ruleset per rule, applied to extracted prose only -- not arbitrary
per-block routing.

## Decisions, and what was rejected

**Semantic flags only, pooled across segments.** Every extracted
segment is linted separately, all flags pool, and the embedded ruleset's
own `blocking_semantic_flags` runs once over the pool. Density is judged
across the file's whole embedded prose the way a ruleset judges a whole
document: eight strings carrying one flag each read exactly as sloppy as
one string carrying eight, and a per-segment threshold would let the
first case through. No blocking policy lives in core -- the plugin
contract's rule, unchanged.

**No auto-fix, ever, for embedded prose.** Splicing rewritten text back
between quote marks is a lossless-rewrite problem: escape sequences,
string prefixes, implicit concatenation, f-string boundaries. Mechanical
violations found in embedded prose are dropped rather than reported,
because a violation the gate can neither fix nor reasonably ask a human
to fix on every write is noise. Revisit only with a genuinely lossless
splice.

**Comments are not extracted.** codewatch already owns comment judgment
(`trivial_comment`, `narrative_comment`, `meta_comment`); a prose
ruleset on the same text would be a second judge with a different
rulebook. And comments are telegraphic fragments -- sentence-shaped
checks misfire on `# fix later`.

**A word-count floor, not a heuristic classifier.** Dict keys, paths,
and format specs are string literals too. Anything under
`MIN_PROSE_WORDS` (4) words is plumbing. Simple, predictable, and wrong
in only one direction (a three-word caption goes unjudged).

**f-strings are joined, with stand-ins at interpolations.** Most
dashboard copy IS f-strings; skipping them would exempt exactly the text
this exists to reach. `f"{n} checks run on {probe}"` is judged as
`"X checks run on X"`.

**Typos are loud, bindings that cannot fire are refused.** An
`embedded_prose` id is validated against the registry at write time by
`save_rules`, the same guarantee host ruleset ids get. A rule whose glob
names an extension no extractor covers is refused outright -- a binding
that can never fire is a gate quietly not doing what its owner believes,
the `.dat`-bypass failure shape. `save_rules` also now preserves every
extra key a stored rule carries (packs had this as a carve-out;
`disable` was already exposed to the same clobber, and `embedded_prose`
would have been next).

**Where it runs.** Three places: the live hook (`pretool_hook.py`),
`stopslop.py lint`, and the git pre-commit gate (`stopslop.py
precommit`). The lint command skips the pass under `--ruleset`; that
flag means "exactly this ruleset and nothing else". The hook and the
pre-commit gate judge the RESULTING file, with a ratchet: deny only
what is deniable AND worse than before. That rule closed two live
cheats. A delta-linted file could accrete slop under the bar, one Edit
at a time. And an Edit fragment never parses as Python, so this pass
skipped every Edit at first. Segments lint joined as one document, so
a document-level check (an em-dash cluster) sees a file's whole
embedded prose. Two simplifications are deliberate. `scan` and the MCP
`lint_text` tool do not run the pass yet. A deny with host and
embedded flags both logs as ONE history event, under the host
ruleset's id; the double-fire dedup would collapse two events.

## Adding a language

Add an extractor to `core/extract.py` and its extension to
`SUPPORTED_EXTENSIONS`. The contract is one function's worth: given
source text, return `[{"line", "text"}, ...]` of prose-sized segments.
Everything downstream -- pooling, policy, hook wiring, config
validation -- is already generic.
