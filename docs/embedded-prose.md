# Embedded prose: a second ruleset for the strings inside code

A routing rule can name a prose ruleset for the code files it matches:

```json
{"glob": "*.py", "ruleset": "codewatch", "embedded_prose": "slopwatch"}
```

The gate then runs both. The host ruleset judges the whole file exactly
as before. The named prose ruleset judges the string literals and
docstrings that `core/extract.py` pulls out. Either gate can deny the
write.

## Why this exists

The routing model had one gap: this project's own UI copy. The
dashboard's own `configure.py` module routes to codewatch, which
judges comments but never string literals. ste100 and slopwatch judge
prose, but only whole `.md`/`.txt`/`.rst` files. The dashboard's
captions -- the text closest to a user's own eyes -- reached no
ruleset at all. A gate named stopslop shipped
screens of prose outside every ruleset's reach. Several sessions of
manual UI-copy review proved this by eye. Each one turned up exactly
the repetition and register drift a prose ruleset flags on its own.

The original pluggable-ruleset plan deferred this as separate
per-block-type routing within one file. Its own note called it a real
feature with real complexity and no need yet. The need arrived. What
shipped is smaller than the deferred plan: one extra ruleset per rule,
applied to extracted prose only, not arbitrary per-block routing.

## Decisions, and the rejected alternatives

**Semantic flags only, pooled across segments.** The gate lints every
extracted segment on its own. All flags pool. The embedded ruleset's
own `blocking_semantic_flags` runs once over that pool. Density counts
across the file's whole embedded prose, the way a ruleset judges a
whole document. Eight strings that each carry one flag read exactly as
sloppy as one string that carries eight. A per-segment threshold lets
the first case through instead. No policy about which flags deny a
write lives in core -- the plugin contract's own rule, unchanged.

**No auto-fix, ever, for embedded prose.** Rewritten text can never
splice back between quote marks without loss. Escape sequences, string
prefixes, implicit concatenation, and f-string boundaries all stand in
the way. The gate drops a mechanical violation found in embedded prose
instead of a report. A violation the gate can neither fix nor
reasonably ask a human to fix, on every write, is only noise. Revisit
this only with a genuinely lossless splice.

**Comments are not extracted.** codewatch already owns comment
judgment (`trivial_comment`, `narrative_comment`, `meta_comment`). A
prose ruleset on the same text becomes a second judge with a different
rulebook. Comments are also telegraphic fragments. A sentence-shaped
check misfires on `# fix later`.

**A word-count floor, not a heuristic classifier.** Dict keys, paths,
and format specs count as string literals too. Anything under
`MIN_PROSE_WORDS` (4) words does not count as prose. Simple,
predictable, and wrong in only one direction: a three-word caption
goes unjudged.

**f-strings join, with a stand-in at each interpolation.** Most
dashboard copy is f-strings. Skip them, and the gate exempts exactly
the text this feature exists to reach. The gate reads
`f"{n} checks run on {probe}"` as `"X checks run on X"`.

**Typos are loud, a binding that cannot fire gets refused.**
`save_rules` checks an `embedded_prose` id against the registry at
write time. A host ruleset id already gets the same guarantee. A rule
whose glob names an extension no extractor covers gets
refused outright. A binding that can never fire leaves a gate quietly
wrong about its own behavior -- the same `.dat`-bypass failure shape.
The `save_rules` function now also keeps every extra key a stored rule
carries. Packs already had this as a carve-out. `disable` was already
exposed to the same clobber. `embedded_prose` was next in line for the
same gap.

**Where it runs.** Three places: the live hook (`pretool_hook.py`),
`stopslop.py lint`, and the git pre-commit gate (`stopslop.py
precommit`). The lint command skips the pass under `--ruleset`. That
flag means "exactly this ruleset and nothing else". The hook and the
pre-commit gate judge the file that results, with a ratchet: deny only
what is deniable AND worse than before. That rule closed two live
cheats. Without the ratchet, a delta-linted file gains slop under the
bar, one Edit at a time. An Edit fragment also never parses as Python,
so this pass skipped every Edit at first. Segments lint joined as one
document, so a document-level check (an em-dash cluster) sees a file's
whole embedded prose. Two simplifications stay deliberate. `scan` and
the MCP `lint_text` tool do not run this pass yet. A deny with host
and embedded flags both logs as ONE history event, under the host
ruleset's own id. The double-fire dedup otherwise collapses two events
into one.

## Add a language

Add an extractor to `core/extract.py` and its extension to
`SUPPORTED_EXTENSIONS`. The contract is one function's worth: given
source text, return `[{"line", "text"}, ...]` of prose-sized segments.
Everything downstream -- how segments pool, the policy, the hook, and
config checks -- is already generic.
