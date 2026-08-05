"""Prose embedded in code: extraction, and the gate pass over it.

The routing model had a crack exactly where this project's own UI copy
lived. configure.py routes to codewatch, which judges comments but never
string literals; ste100 and slopwatch judge prose but only whole
.md/.txt/.rst files. So the dashboard's captions -- prose by any
definition, and the most user-facing text in the product -- reached no
ruleset at all, and a gate named stopslop shipped screens of text it
could never lint. The original pluggable-ruleset plan deferred this as
"per-block-type ruleset mixing within one file"; the deferral ended when
a manual UI-copy audit spent several sessions doing, by eye, exactly
what these fifty lines do. See docs/embedded-prose.md for the decision
record.

A routing rule opts in by naming a second, prose ruleset for the code
files it matches:

    {"glob": "*.py", "ruleset": "codewatch", "embedded_prose": "slopwatch"}

The gate then runs BOTH: the host ruleset over the whole file exactly as
before, and the named ruleset over the string literals and docstrings
extracted here. Either denying denies. No rule names embedded_prose by
default -- an unconfigured clone behaves exactly as it always has, the
same invariant every other knob in core/config.py keeps.

What is deliberately NOT extracted, and why:

- Comments. codewatch already owns comment judgment (trivial_comment,
  narrative_comment, meta_comment); sending comments to a prose ruleset
  too would put two judges on one text. And comments are telegraphic
  fragments -- sentence-shaped checks misfire on "# fix later".
- Strings under MIN_PROSE_WORDS words. Dict keys, paths, format specs
  and identifiers are string literals too; a word-count floor is the
  difference between linting UI copy and linting plumbing.
- Mechanical fixes. Splicing rewritten prose back between quote marks is
  a lossless-rewrite problem (escape sequences, string prefixes,
  implicit concatenation) this deliberately does not take on; embedded
  prose is judged, never rewritten -- see embedded_prose_flags.
"""
import ast
import os

# Languages an extractor exists for, keyed by file extension. A rule
# naming embedded_prose for anything else is refused at WRITE time by
# core.config.save_rules -- the loud-on-typo guarantee ruleset ids
# already get, because a binding that can never fire is a gate quietly
# not doing what its owner believes (the .dat-bypass failure shape).
SUPPORTED_EXTENSIONS = {".py"}

# A string literal is prose worth judging once it reads like a sentence
# rather than a key. Four words keeps "block_flag_count_threshold" and
# "%Y-%m-%d %H:%M:%S" out while keeping real captions in.
MIN_PROSE_WORDS = 4

# An f-string's interpolations become this stand-in, so its constant
# parts still read as one sentence ("{n} checks run on {probe}" ->
# "X checks run on X"). Most of a dashboard's copy IS f-strings;
# skipping them would exempt exactly the text this exists to reach.
STAND_IN = "X"


def prose_segments(text, extension):
    """[{"line", "text"}, ...] for every prose-sized string literal and
    docstring in `text`, oldest-first. Empty for an unsupported language,
    and empty for source that does not parse -- a half-written draft
    must never crash the gate (same never-break-the-gate posture as
    history logging)."""
    if extension not in SUPPORTED_EXTENSIONS:
        return []
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        return []

    segments, fstring_parts = [], set()
    # JoinedStr first: its constant pieces are ast.Constant nodes too,
    # and must join into one segment rather than also reporting alone.
    for node in ast.walk(tree):
        if not isinstance(node, ast.JoinedStr):
            continue
        pieces = []
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                fstring_parts.add(id(value))
                pieces.append(value.value)
            else:
                pieces.append(STAND_IN)
        _append(segments, "".join(pieces), node.lineno)
    for node in ast.walk(tree):
        if (isinstance(node, ast.Constant) and isinstance(node.value, str)
                and id(node) not in fstring_parts):
            _append(segments, node.value, node.lineno)
    segments.sort(key=lambda s: s["line"])
    return segments


def _append(segments, value, line):
    if len(value.split()) >= MIN_PROSE_WORDS:
        segments.append({"line": line, "text": value})


def embedded_prose_pool(text, extension, module, file_path=None):
    """Every semantic flag for the prose embedded in a code file, judged
    as ONE document.

    Segments join with blank lines and lint once. Per-segment linting
    had a structural blind spot: document-level checks (em-dash
    clustering, cross-sentence patterns) could never fire, because no
    single caption holds a cluster even when the rendered page holds
    dozens -- the file's total was unreachable by construction. Joining
    also means eight strings carrying one flag each read exactly as
    sloppy as one string carrying eight. Each flag that names a sentence
    is traced back to its segment and carries that segment's starting
    line as "embedded_line"; a document-level flag with no sentence of
    its own stays file-scoped. Mechanical violations are dropped, not
    fixed (the splice-back problem, see the module docstring).
    `file_path` passes through so a rule's vocabulary packs feed the
    embedded ruleset's lists the same way they feed the host's."""
    segments = prose_segments(text, extension)
    if not segments:
        return []
    joined = "\n\n".join(s["text"] for s in segments)
    result = module.lint_and_gate(joined, file_path=file_path)
    pooled = []
    for flag in result["semantic_flags"]:
        flag = dict(flag)
        sentence = flag.get("text") or ""
        for segment in segments:
            if sentence and sentence in segment["text"]:
                flag["embedded_line"] = segment["line"]
                break
        pooled.append(flag)
    return pooled


def embedded_prose_flags(text, extension, module, file_path=None):
    """The BLOCKING subset of embedded_prose_pool, decided by the
    embedded ruleset's OWN deny policy -- the plugin contract's core
    principle, unchanged: no policy lives here."""
    return module.blocking_semantic_flags(
        embedded_prose_pool(text, extension, module, file_path=file_path))


def rule_embedded_ruleset(rule, registry):
    """The embedded-prose ruleset module a routing rule names, or None.
    Raises registry.UnknownRulesetError on a typo'd id -- the same loud
    failure resolve_ruleset gives a typo'd host id, for the same reason."""
    embedded_id = (rule or {}).get("embedded_prose")
    if not embedded_id:
        return None
    return registry.get_ruleset(embedded_id)


def glob_extension_supported(glob):
    """False only when `glob` names a definite extension no extractor
    covers. A glob with no extension at all (".claude/*") stays True:
    the per-file extension check in prose_segments already no-ops it."""
    ext = os.path.splitext(glob)[1]
    return not ext or ext in SUPPORTED_EXTENSIONS
