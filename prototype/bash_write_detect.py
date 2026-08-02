#!/usr/bin/env python3
"""Best-effort extraction of (target_file, payload_text) from Bash commands
that write to a target file via a heredoc (cat/tee, either direction --
`cat <<EOF | tee file.md` or `tee file.md <<EOF`), a simple echo/printf
redirect, or echo/printf piped into tee -- the bypass path identified early
in this project: the Write/Edit gate does nothing against `cat > file.md
<<EOF`.

The target extension set is a parameter, not a hardcoded constant --
generalized during the pluggable-ruleset refactor so this detector isn't
tied to STE100's .md/.txt/.rst scope. Callers pass whatever extensions
core.config.known_extensions() resolves for the active config.

Deliberately conservative. This is NOT a shell parser -- it's targeted
regex matching for the highest-confidence write patterns. Anything ambiguous
(command substitution, variable interpolation in the target path, multiple
heredocs, non-string echo arguments) falls through to "not detected" rather
than guessing, on purpose: a false positive here blocks ordinary bash usage
and would make the gate untrustworthy; a false negative just leaves that
specific bypass path uncaught, same as before this file existed. Still not
covered as of this writing: printf with an actual format string (multiple
args, not a single literal), and multi-line `cat >>` appends without a
heredoc. No auto-fix/rewrite is attempted for Bash commands -- only detect-
and-deny -- because rewriting a shell command string correctly (preserving
quoting/escaping) is real additional risk not yet taken on.
"""
import re

DEFAULT_EXTENSIONS = (".md", ".txt", ".rst")

# Guard against commands whose complexity makes extraction unreliable --
# command substitution, multiple heredocs, or piping into something else
# all mean "don't trust a simple regex parse here."
_TOO_COMPLEX_RE = re.compile(r"\$\(|`|<<.*<<")


def _target_re(extensions):
    exts = "|".join(re.escape(e.lstrip(".")) for e in extensions)
    return r"[^\s<>|;&]+\.(?:" + exts + r")"


def extract_heredoc_write(command, extensions=DEFAULT_EXTENSIONS):
    if _TOO_COMPLEX_RE.search(command):
        return None
    heredoc_start = re.search(r"<<(-)?\s*(['\"]?)(\w+)\2", command)
    if not heredoc_start:
        return None
    dash, quote, marker = heredoc_start.groups()

    line_end = command.find("\n", heredoc_start.end())
    if line_end == -1:
        return None
    header_line = command[:line_end]
    if not re.search(r"\b(cat|tee)\b", header_line):
        return None
    target_match = re.search(r"(" + _target_re(extensions) + r")\b", header_line)
    if not target_match:
        return None
    target = target_match.group(1)

    body_start = line_end + 1
    if dash:
        close_re = re.compile(r"^\t*" + re.escape(marker) + r"\s*$", re.MULTILINE)
    else:
        close_re = re.compile(r"^" + re.escape(marker) + r"\s*$", re.MULTILINE)
    close_match = close_re.search(command, body_start)
    if not close_match:
        return None
    body = command[body_start:close_match.start()]
    if dash:
        body = "\n".join(line.lstrip("\t") for line in body.split("\n"))
    # An UNQUOTED heredoc marker (<<EOF) undergoes shell variable/command
    # substitution inside the body -- $VAR, $(...), backticks all expand at
    # runtime to content we can't know statically. A QUOTED marker
    # (<<'EOF' or <<"EOF") disables all of that, so the body is guaranteed
    # literal. Only lint when we can be sure the text is real.
    if not quote and re.search(r"\$|`", body):
        return None
    return target, body


def extract_echo_write(command, extensions=DEFAULT_EXTENSIONS):
    if _TOO_COMPLEX_RE.search(command):
        return None
    # Only a single quoted string argument -- multi-arg, unquoted, or
    # variable-containing echo/printf commands are not matched at all.
    m = re.match(
        r"^\s*(echo|printf)\b\s+(?:-\w+\s+)?(['\"])(.*?)\2\s*(>>?)\s*(" + _target_re(extensions) + r")\s*$",
        command)
    if not m:
        return None
    _, quote, text, _redir, target = m.groups()
    # Single-quoted strings are always literal in shell; double-quoted
    # strings undergo $VAR/`...` expansion, so the actual runtime content
    # isn't known statically. Only trust single-quoted, or double-quoted
    # with no expansion markers present.
    if quote == '"' and re.search(r"\$|`", text):
        return None
    return target, text


def extract_piped_tee_write(command, extensions=DEFAULT_EXTENSIONS):
    """echo/printf '...' | tee [-a] file.md -- confirmed gap: extract_echo_write
    only matches a >/>> redirect, not a pipe into tee, so this pattern reached
    extract_bash_write and returned None (silently undetected) even though
    heredoc-piped-to-tee (cat <<EOF | tee file.md) and tee-with-heredoc
    (tee file.md <<EOF) both already worked via extract_heredoc_write's
    header-line scan. Same conservative single-quoted-string approach as
    extract_echo_write -- multi-arg, unquoted, or variable-containing forms
    are not matched at all."""
    if _TOO_COMPLEX_RE.search(command):
        return None
    m = re.match(
        r"^\s*(echo|printf)\b\s+(?:-\w+\s+)?(['\"])(.*?)\2\s*\|\s*tee\b\s+(?:-\w+\s+)?("
        + _target_re(extensions) + r")\s*$",
        command)
    if not m:
        return None
    _, quote, text, target = m.groups()
    if quote == '"' and re.search(r"\$|`", text):
        return None
    return target, text


def extract_bash_write(command, extensions=DEFAULT_EXTENSIONS):
    """Try all three patterns, return (target, payload) or None."""
    return (extract_heredoc_write(command, extensions)
            or extract_echo_write(command, extensions)
            or extract_piped_tee_write(command, extensions))
