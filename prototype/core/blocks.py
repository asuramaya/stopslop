"""Ruleset-agnostic text structure: splitting a document into blocks (code
fences, headers, list items, paragraphs, blank lines), and splitting a block
of text into sentences/words. Moved out of ste100_lint.py during the
pluggable-ruleset refactor -- none of this logic is specific to ASD-STE100's
rules; it's the same "don't lint inside a code fence, don't flatten a
document into one giant sentence" plumbing any prose-linting ruleset needs.

split_into_blocks is shared by detection and auto-fix code within a ruleset
(e.g. ste100's lint_and_gate/apply_mechanical_fixes both use it) so the two
can't silently disagree about block boundaries -- an earlier, ad hoc version
of this had exactly that bug: a real document with a header + list + code
fence got flattened into one 36-word "sentence" by a flat tokenizer and was
denied on a false length violation, only found by testing an actual
structured document live through the hook.
"""
import re

_HEADER_RE = re.compile(r"^#{1,6}\s")
_LIST_ITEM_RE = re.compile(r"^(\s*(?:[-*+]|\d+[.)])\s+)(.*)$")
_FENCE_RE = re.compile(r"^```")


def tokenize_sentences(text):
    """Naive regex sentence splitter -- fast, not spaCy-accurate. Deliberately
    naive so it's obvious where it breaks on abbreviations rather than
    hiding that behind a heavier dependency."""
    raw = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text.strip())
    return [s.strip() for s in raw if s.strip()]


def words(sentence):
    return re.findall(r"[A-Za-z']+", sentence)


def list_item_match(line):
    """Exposed for ruleset code that needs to tell a list marker from its
    text (e.g. to force procedure-context rules onto numbered steps)."""
    return _LIST_ITEM_RE.match(line)


def split_into_blocks(text):
    """Split a document into (block_type, content) pairs: 'fence', 'header',
    'list_item', 'paragraph', or 'blank'."""
    lines = text.split("\n")
    blocks = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if _FENCE_RE.match(stripped):
            fence_lines = [line]
            i += 1
            while i < len(lines):
                fence_lines.append(lines[i])
                is_close = _FENCE_RE.match(lines[i].strip())
                i += 1
                if is_close:
                    break
            blocks.append(("fence", "\n".join(fence_lines)))
            continue
        if not stripped:
            blocks.append(("blank", line))
            i += 1
            continue
        if _HEADER_RE.match(stripped):
            blocks.append(("header", line))
            i += 1
            continue
        m = _LIST_ITEM_RE.match(line)
        if m:
            blocks.append(("list_item", line))
            i += 1
            continue

        para_lines = []
        while i < len(lines):
            s2 = lines[i].strip()
            if not s2 or _FENCE_RE.match(s2) or _HEADER_RE.match(s2) or _LIST_ITEM_RE.match(lines[i]):
                break
            para_lines.append(lines[i])
            i += 1
        blocks.append(("paragraph", " ".join(l.strip() for l in para_lines)))

    return blocks


# Regex constants exposed for rulesets that need to replicate the exact
# header/list-item boundary logic (e.g. ste100's apply_mechanical_fixes,
# which re-matches _LIST_ITEM_RE to split a list item's marker from its text).
HEADER_RE = _HEADER_RE
LIST_ITEM_RE = _LIST_ITEM_RE
FENCE_RE = _FENCE_RE
