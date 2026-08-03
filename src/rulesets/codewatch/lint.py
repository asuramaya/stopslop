#!/usr/bin/env python3
"""codewatch: a ruleset for the tells AI coding agents leave in Python
source, not prose. Where ste100 and slopwatch both gate WRITING (docs,
READMEs, commit-adjacent text), codewatch gates CODE -- proof the plugin
contract generalizes past the text-document domain entirely, the same
point slopwatch already proved for a second writing style.

Line-based, not AST-based, on purpose: stopslop gates a single file's text
at write time, the same regex-over-parser tradeoff already used
everywhere else in this project (over-flag a real edge case rather than
miss a genuine one -- see ste100's own -ing check for the precedent).
Scoped to Python only for now, this project's own primary language and
the one every check here has been tested against directly -- not a
statement that the underlying tells are Python-specific.

Ported from scanaislop/aislop (MIT) -- see NOTICE. aislop is a much larger,
AST-based, multi-language tool; these four are line-based translations of
its "ai-slop" engine's pattern DATA (its narrative-comments-patterns.ts,
meta-comment.ts, and exceptions.ts), not its detection machinery:
  - trivial_comment    (semantic)  a comment that only restates the next line
  - narrative_comment    (semantic)  decorative separators, section headers,
    cross-reference commentary, step-by-step narration
  - meta_comment           (semantic)  a comment about the plan/spec/ticket,
    or before/after narration that belongs in a commit message, not source
  - swallowed_exception      (semantic, always blocks)  bare except: pass

Own words, informed by aislop's own docs/rules.md (MIT) describing these
rule NAMES and what they catch, but not ported from its TypeScript:
  - mutable_default_arg  (semantic)  def f(x=[]): a default shared across calls
  - print_debug            (semantic)  leftover print() in an importable library
    module; a script with a real `if __name__ == "__main__":` guard is exempt
    (see _is_script) -- its console output is the point, not a leftover
  - todo_stub                (semantic)  an untracked TODO/FIXME/HACK
  - generic_naming             (semantic)  helper_1, data2, temp1
  - tautological_assert          (semantic)  assert True, can never fail
  - constant_condition             (semantic)  if True: / if False:

blocking_semantic_flags() here is a THIRD distinct policy, proving the
plugin contract doesn't just support "exclusion list" (ste100) and "count
threshold" (slopwatch") shapes: swallowed_exception always blocks, since a
silently-eaten exception is a real correctness risk, not a style
preference -- everything else uses the same count-threshold shape
slopwatch already established.
"""
import re

from core import config as _core_config, paths as _paths, terms as _terms

TRACKED_EXTENSIONS = (".py",)

# Every "kind" string this ruleset's checks can produce -- see
# rulesets/slopwatch/lint.py's ALL_CHECK_IDS for the identical pattern and
# rationale. rulesets/codewatch/__init__.py's list_checks()/
# set_enabled_checks() expose this as the modularity surface.
ALL_CHECK_IDS = frozenset({
    "trivial_comment", "narrative_comment", "meta_comment", "swallowed_exception",
    "mutable_default_arg", "print_debug", "todo_stub", "generic_naming",
    "tautological_assert", "constant_condition",
})


def _enabled_check_ids():
    try:
        project_root = _paths.find_project_root(__file__)
        disabled = set(_core_config.disabled_checks(project_root, "codewatch"))
    except Exception:
        return set(ALL_CHECK_IDS)
    return ALL_CHECK_IDS - disabled


def _custom_terms(list_id, file_path=None):
    """The non-built-in layers (packs, then the project's own registrations)
    for one term list -- same never-cache-it, read-fresh-every-call
    philosophy as _enabled_check_ids(). Falls back to none (never breaks a
    check) if project root can't be resolved. See slopwatch's identical
    helper and core.config.packs_for_path for why file_path matters."""
    try:
        project_root = _paths.find_project_root(__file__)
        layers = _terms.resolve(TERM_LISTS[list_id], project_root, "codewatch",
                                 list_id, file_path=file_path)
        return sorted(set(layers["packs"]) | set(layers["project"]))
    except Exception:
        return []


DEFAULT_OPTIONS = {
    "block_flag_count_threshold": 4,
}


def _options():
    opts = dict(DEFAULT_OPTIONS)
    try:
        project_root = _paths.find_project_root(__file__)
        overrides = _core_config.ruleset_options(project_root, "codewatch")
    except Exception:
        return opts
    for key, value in overrides.items():
        if key in opts and isinstance(value, type(opts[key])):
            opts[key] = value
    return opts

# --- trivial_comment (semantic) -- ported from scanaislop/aislop (MIT) -----
_TRIVIAL_VERB_STEMS = (
    "Import|Defin|Initializ|Setting|Set up|Setup|Return|Check|Loop|Iterat|"
    "Creat|Updat|Delet|Remov|Handl|Get|Fetch|Increment|Decrement|Writ|Runn|"
    "Run|Pars|Execut|Extract|Sav|Load|Build|Start|Stopp|Stop|Cleanup|Clean up|"
    "Configur|Validat|Process|Queue|Fire|Emit|Dispatch|Log|Print|Render"
)
_TRIVIAL_COMMENT_RE = re.compile(
    r"^#\s*This (?:function|method|class) (?:will |is used to )?|"
    r"^#\s*(?:" + _TRIVIAL_VERB_STEMS + r")(?:e|es|ing|s)?\b", re.IGNORECASE)
_EXPLANATORY_KEYWORDS_RE = re.compile(
    r"\b(?:because|since|note|todo|fixme|hack|warn|warning|workaround|caveat|"
    r"important|assumes?|if|when|unless|until|only|except|otherwise|needs?|"
    r"must|should|ensure|avoid|prevent|requires?)\b", re.IGNORECASE)
_COMMENTED_CODE_CHARS_RE = re.compile(r"[({=;}\]>]")
_DECORATIVE_CHARS_RE = re.compile(r"[─━═╌╍┄┅│┃]")
_LEADING_DASHES_RE = re.compile(r"^-{3,}|─{3,}")
MAX_TRIVIAL_COMMENT_LENGTH = 60


def check_trivial_comment(line, next_line):
    stripped = line.strip()
    if not stripped.startswith("#") or stripped.startswith("#!"):
        return []
    body = stripped[1:].strip()
    if len(body) > MAX_TRIVIAL_COMMENT_LENGTH:
        return []
    if _EXPLANATORY_KEYWORDS_RE.search(body):
        return []
    if "(" in body and ")" in body:
        return []
    if _COMMENTED_CODE_CHARS_RE.search(body):
        return []
    if next_line is not None and next_line.strip() == "":
        return []
    if _DECORATIVE_CHARS_RE.search(body) or _LEADING_DASHES_RE.match(body):
        return []
    if _TRIVIAL_COMMENT_RE.match(stripped):
        return [{"phrase": stripped, "rule": "codewatch.trivial_comment", "auto_fix": False,
                  "note": "comment restates the code below it -- cut it, or say why instead"}]
    return []


# --- narrative_comment (semantic) -- ported from scanaislop/aislop (MIT) ---
_DECORATIVE_SEPARATOR_RE = re.compile(r"^#\s*[-=─━~_*]{6,}\s*$")
_SECTION_HEADER_RE = re.compile(r"^#\s*(Phase|Step|Section|Part)\s+\d+\s*[:.\-]", re.IGNORECASE)
_CROSS_REFERENCE_RES = [
    re.compile(r"\bwill then be\b", re.IGNORECASE),
    re.compile(r"\bcalled from\b", re.IGNORECASE),
    re.compile(r"\bcalled later\b", re.IGNORECASE),
    re.compile(r"\bsee (?:above|below|later|earlier)\b", re.IGNORECASE),
    re.compile(r"\breplaces the\b", re.IGNORECASE),
    re.compile(r"\bmatches the one\b", re.IGNORECASE),
    re.compile(r"\bwe moved\b", re.IGNORECASE),
    re.compile(r"\bwe used to\b", re.IGNORECASE),
    re.compile(r"\brefactor(?:ed)? from\b", re.IGNORECASE),
]
_JUSTIFICATION_OPENER_RES = [
    re.compile(r"^#\s*(?:The idea here|The trick is|This was needed|Originally,?)", re.IGNORECASE),
    re.compile(r"^#\s*This\s+(?:function|method|class|module|component|hook|util|helper|handler|service)\b",
               re.IGNORECASE),
    re.compile(r"^#\s*It\s+(?:does|handles|takes|returns|processes|reads|writes|sends|fetches|"
               r"loads|creates|deletes|updates|parses|validates)\b", re.IGNORECASE),
    re.compile(r"^#\s*(?:First|Then|Finally|Next|Lastly|Subsequently),?\s+(?:it|we|the\s+"
               r"(?:function|method|class))\b", re.IGNORECASE),
]


def check_narrative_comment(line):
    stripped = line.strip()
    if not stripped.startswith("#") or stripped.startswith("#!"):
        return []
    if _DECORATIVE_SEPARATOR_RE.match(stripped):
        return [{"phrase": stripped, "rule": "codewatch.narrative_comment", "auto_fix": False,
                  "note": "decorative comment separator -- code needs no banner between sections"}]
    if _SECTION_HEADER_RE.match(stripped):
        return [{"phrase": stripped, "rule": "codewatch.narrative_comment", "auto_fix": False,
                  "note": "\"Phase/Step N\" narration -- that belongs in a commit message or a plan doc"}]
    for rx in _CROSS_REFERENCE_RES:
        if rx.search(stripped):
            return [{"phrase": stripped, "rule": "codewatch.narrative_comment", "auto_fix": False,
                      "note": "cross-reference commentary about other code -- link it or cut it"}]
    for rx in _JUSTIFICATION_OPENER_RES:
        if rx.match(stripped):
            return [{"phrase": stripped, "rule": "codewatch.narrative_comment", "auto_fix": False,
                      "note": "step-by-step narration of what the code does -- the code already says this"}]
    return []


# --- meta_comment (semantic) -- ported from scanaislop/aislop (MIT) --------
_PLAN_REFERENCE_RES = [
    re.compile(r"^#\s*(?:stage|step|phase)\s+\d+\s*[:.\-]", re.IGNORECASE),
    re.compile(r"\bstep\s+\d+\s+of\s+the\s+plan\b", re.IGNORECASE),
    re.compile(r"\bas\s+(?:per|requested)\s+(?:the\s+)?(?:requirements?|spec|task|ticket|prompt|instructions?)\b",
               re.IGNORECASE),
    re.compile(r"\bper\s+the\s+(?:spec|requirements?|task|ticket|plan|prompt|instructions?)\b", re.IGNORECASE),
    re.compile(r"\bfrom\s+the\s+(?:task|todo|plan|spec|ticket|prompt|requirements?)\b", re.IGNORECASE),
    re.compile(r"\bas\s+(?:instructed|specified|outlined)\s+(?:above|below|in\s+the)\b", re.IGNORECASE),
]
_BEFORE_AFTER_RES = [
    re.compile(r"\bpreviously[,:]?\s+(?:this|we|it|the)\b", re.IGNORECASE),
    re.compile(r"\bused\s+to\s+(?:be|use|call|return|do|have|rely)\b", re.IGNORECASE),
    re.compile(r"\bchanged\s+(?:\w+\s+){0,3}from\s+.+\bto\b", re.IGNORECASE),
    re.compile(r"\bno\s+longer\s+(?:needed|used|required|necessary|calls?|returns?|does)\b", re.IGNORECASE),
    re.compile(r"\bwe\s+(?:now|used\s+to)\s+(?:no\s+longer\s+)?(?:use|call|return|do|have)\b", re.IGNORECASE),
    re.compile(r"\breplaced\s+the\s+(?:old|previous|former)\b", re.IGNORECASE),
    re.compile(r"\b(?:was|were)\s+(?:renamed|moved|removed|refactored|extracted)\s+(?:from|to|out\s+of)\b",
               re.IGNORECASE),
]
_META_WHY_OR_TODO_RE = re.compile(
    r"\b(?:because|since|otherwise|todo|fixme|hack|note:|reason:|workaround|see\s+(?:issue|#))\b",
    re.IGNORECASE)


def check_meta_comment(line):
    stripped = line.strip()
    if not stripped.startswith("#") or stripped.startswith("#!"):
        return []
    if _META_WHY_OR_TODO_RE.search(stripped):
        return []  # real WHY context or a tracked TODO stays
    for rx in _PLAN_REFERENCE_RES:
        if rx.search(stripped):
            return [{"phrase": stripped, "rule": "codewatch.meta_comment", "auto_fix": False,
                      "note": "reference to the plan/spec/ticket this was written from -- "
                              "belongs in the commit message, not the source"}]
    for rx in _BEFORE_AFTER_RES:
        if rx.search(stripped):
            return [{"phrase": stripped, "rule": "codewatch.meta_comment", "auto_fix": False,
                      "note": "before/after narration of how the code changed -- "
                              "that belongs in a commit message or PR diff, not source"}]
    return []


# --- swallowed_exception (semantic, always blocks) -- ported from ----------
# scanaislop/aislop (MIT)
_PYTHON_SWALLOWED_EXCEPT_RE = re.compile(r"^except(?:\s+[\w.]+)?\s*(?:as\s+\w+)?\s*:\s*$")
_INTENTIONAL_IGNORE_NAMES = {"ignored", "ignore", "tolerated", "expected", "unused",
                              "_", "_e", "_err", "_ex"}
_EXCEPT_AS_NAME_RE = re.compile(r"^except(?:\s+[\w.]+)?\s+as\s+(\w+)\s*:\s*$")


def check_swallowed_exception(lines, i):
    """lines[i] is an `except ...:` line; flags it if the next non-blank
    line is exactly `pass` and the caught exception isn't named as one of
    the conventional intentional-ignore names ("_", "ignored", ...)."""
    line = lines[i].rstrip()
    stripped = line.strip()
    if not _PYTHON_SWALLOWED_EXCEPT_RE.match(stripped):
        return []
    name_match = _EXCEPT_AS_NAME_RE.match(stripped)
    if name_match and name_match.group(1).lower() in _INTENTIONAL_IGNORE_NAMES:
        return []
    j = i + 1
    while j < len(lines) and lines[j].strip() == "":
        j += 1
    if j < len(lines) and lines[j].strip() == "pass":
        return [{"phrase": stripped, "rule": "codewatch.swallowed_exception", "auto_fix": False,
                  "note": "bare except with pass swallows the error silently -- "
                          "log it, re-raise it, or name why it's safe to ignore"}]
    return []


# --- mutable_default_arg (semantic) -- own words --------------------------
_DEF_LINE_RE = re.compile(r"^\s*(?:async\s+)?def\s+\w+\s*\(")
_MUTABLE_DEFAULT_RE = re.compile(r"(\w+)\s*=\s*(\[\]|\{\}|set\(\))")


def check_mutable_default_arg(line):
    if not _DEF_LINE_RE.match(line):
        return []
    return [{"phrase": f"{m.group(1)}={m.group(2)}", "rule": "codewatch.mutable_default_arg",
              "auto_fix": False,
              "note": "mutable default argument -- shared across every call, use None and "
                      "create the real default inside the function"}
            for m in _MUTABLE_DEFAULT_RE.finditer(line)]


# --- print_debug (semantic) -- own words -----------------------------------
_PRINT_DEBUG_RE = re.compile(r"^\s*print\(")
_MAIN_GUARD_RE = re.compile(r"^if\s+__name__\s*==\s*[\"']__main__[\"']\s*:")
_DEF_OR_CLASS_RE = re.compile(r"^\s*(?:async\s+def|def|class)\s")


def _is_script(lines):
    """True for a file whose console output is its own point, not a debug
    leftover -- two shapes, both live-verified against this project's own
    real files by stopslop.py scan (see docs/incidents/ for the discipline
    this project applies to any claim like that):

    1. A real `if __name__ == "__main__":` guard: meant to be run directly,
       not just imported (build_glossary_pack_*.py, build_dictionary.py).

    2. No function or class defined anywhere: a bare top-level launcher
       (mcp_launch.py) has no importable API surface at all -- every line
       runs identically whether the file is imported or executed, so
       there's no "this is really a library, and something leaked into it"
       question for a `__main__` guard to normally answer.

    A module that defines functions/classes but has no `__main__` guard
    keeps the original, stricter behavior -- a stray print() deep in
    otherwise-importable code is still worth flagging."""
    if any(_MAIN_GUARD_RE.match(line) for line in lines):
        return True
    return not any(_DEF_OR_CLASS_RE.match(line) for line in lines)


def check_print_debug(line, is_script):
    if is_script:
        return []
    if _PRINT_DEBUG_RE.match(line):
        return [{"phrase": line.strip(), "rule": "codewatch.print_debug", "auto_fix": False,
                  "note": "leftover print() -- use logging, or remove it before this ships"}]
    return []


# --- todo_stub (semantic) -- own words --------------------------------------
_TODO_STUB_RE = re.compile(r"#\s*(TODO|FIXME|HACK)\b[:\s]*(.*)$", re.IGNORECASE)
_TRACKING_REF_RE = re.compile(r"#\d+|[A-Z]{2,}-\d+|https?://", re.IGNORECASE)


def check_todo_stub(line):
    m = _TODO_STUB_RE.search(line)
    if not m:
        return []
    rest = m.group(2)
    if _TRACKING_REF_RE.search(rest):
        return []  # links a real tracking issue -- not an orphaned stub
    return [{"phrase": m.group(0).strip(), "rule": "codewatch.todo_stub", "auto_fix": False,
              "note": "untracked TODO/FIXME/HACK -- link a tracking issue, or resolve it now"}]


# --- generic_naming (semantic) -- own words --------------------------------
GENERIC_NAME_STEMS = {"helper", "data", "temp", "tmp", "value", "item",
                       "obj", "thing", "foo", "bar", "result", "util"}
# codewatch's one term list -- same shared shape (core/terms.py) as
# slopwatch's five and ste100's project vocabulary, just fewer of them.
# A DENY list: these stems are the thing being flagged.
#
# This ruleset having no ALLOW list is a real gap, not a design choice --
# "`data` and `handler` are fine in THIS repo" is an obviously reasonable
# thing to want, and it was structurally impossible to express before,
# because allow-shaped storage was spelled "glossary" and glossary was
# ste100's word. Adding one is now a TERM_LISTS entry with
# polarity="allow", not a new mechanism.
TERM_LISTS = {
    "generic_naming": {
        "content_kind": "word",
        # Which CHECK this list feeds. Declared, not inferred from the
        # id: ste100's three lists all feed one check, so any UI that
        # paired them by name would show that check as having no
        # vocabulary at all. A list naming its check is fine (both are
        # internal to this ruleset); a PACK naming its consumer was not,
        # because a pack is shared content -- see core/glossary_packs.
        "feeds": "generic_naming",
        "label": "Generic name stems",
        "description": "Placeholder-sounding identifier stems (helper, data, temp...).",
        "polarity": "deny", "accepts_packs": True,
        "built_ins": GENERIC_NAME_STEMS,
    },
}


def check_generic_naming(line, extra=()):
    if not _DEF_LINE_RE.match(line) and "=" not in line:
        return []
    stems = GENERIC_NAME_STEMS | set(extra)
    pattern = re.compile(r"\b(?:" + "|".join(re.escape(s) for s in stems) + r")_?\d+\b", re.IGNORECASE)
    return [{"word": m.group(0), "rule": "codewatch.generic_naming", "auto_fix": False,
              "note": "generic, numbered name -- say what the value actually is"}
            for m in pattern.finditer(line)]


# --- tautological_assert / constant_condition (semantic) -- own words ------
_TAUTOLOGICAL_ASSERT_RE = re.compile(r"^\s*assert\s+True\s*$")
_CONSTANT_CONDITION_RE = re.compile(r"^\s*(?:if|while)\s+(True|False)\s*:\s*$")


def check_tautological_assert(line):
    if _TAUTOLOGICAL_ASSERT_RE.match(line):
        return [{"phrase": line.strip(), "rule": "codewatch.tautological_assert", "auto_fix": False,
                  "note": "assert True can never fail -- assert the real condition, or remove it"}]
    return []


def check_constant_condition(line):
    m = _CONSTANT_CONDITION_RE.match(line)
    if m:
        return [{"word": m.group(1), "rule": "codewatch.constant_condition", "auto_fix": False,
                  "note": f"condition is always {m.group(1)} -- dead branch, or leftover debug code"}]
    return []


def lint_and_gate(text, context=None, file_path=None):
    lines = text.split("\n")
    semantic = []
    is_script = _is_script(lines)
    extra_generic_names = _custom_terms("generic_naming", file_path)  # once per call, not per line

    for i, line in enumerate(lines):
        next_line = lines[i + 1] if i + 1 < len(lines) else None
        for v in check_trivial_comment(line, next_line):
            semantic.append({"kind": "trivial_comment", "label": v["phrase"], "detail": v, "text": line})
        for v in check_narrative_comment(line):
            semantic.append({"kind": "narrative_comment", "label": v["phrase"], "detail": v, "text": line})
        for v in check_meta_comment(line):
            semantic.append({"kind": "meta_comment", "label": v["phrase"], "detail": v, "text": line})
        for v in check_swallowed_exception(lines, i):
            semantic.append({"kind": "swallowed_exception", "label": v["phrase"], "detail": v, "text": line})
        for v in check_mutable_default_arg(line):
            semantic.append({"kind": "mutable_default_arg", "label": v["phrase"], "detail": v, "text": line})
        for v in check_print_debug(line, is_script):
            semantic.append({"kind": "print_debug", "label": v["phrase"], "detail": v, "text": line})
        for v in check_todo_stub(line):
            semantic.append({"kind": "todo_stub", "label": v["phrase"], "detail": v, "text": line})
        for v in check_generic_naming(line, extra_generic_names):
            semantic.append({"kind": "generic_naming", "label": v["word"], "detail": v, "text": line})
        for v in check_tautological_assert(line):
            semantic.append({"kind": "tautological_assert", "label": v["phrase"], "detail": v, "text": line})
        for v in check_constant_condition(line):
            semantic.append({"kind": "constant_condition", "label": v["word"], "detail": v, "text": line})

    # Every check above runs unconditionally; a disabled check's own flags
    # are dropped here in one place rather than guarding all 10 call sites.
    enabled = _enabled_check_ids()
    semantic = [f for f in semantic if f["kind"] in enabled]

    status = "clean" if not semantic else "semantic_flags"
    return {
        "status": status,
        "sentence_count": len(lines),
        "mechanical_violations": [],
        "semantic_flags": semantic,
    }


def blocking_semantic_flags(semantic_flags):
    """A third distinct policy, alongside ste100's exclusion list and
    slopwatch's pure count threshold: swallowed_exception always blocks
    (a real correctness risk, not a style preference); everything else
    blocks only past the configured density threshold (4 by default, see
    DEFAULT_OPTIONS)."""
    always_blocking = [f for f in semantic_flags if f["kind"] == "swallowed_exception"]
    if always_blocking:
        return semantic_flags
    if len(semantic_flags) >= _options()["block_flag_count_threshold"]:
        return semantic_flags
    return []


def apply_mechanical_fixes(text, file_path=None):
    """No mechanical checks exist here -- every codewatch flag needs a
    human or model decision (cut the comment, name the exception, rename
    the variable), never a blind rewrite. Present for contract completeness."""
    return text
