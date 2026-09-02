#!/usr/bin/env python3
"""Turn a Vale style package into stopslop custom checks.

Vale is the mature prose-linting infrastructure and several people have
already encoded AI writing tells as Vale rules. Those rules are data --
a message, a level, and a set of tokens or raw patterns -- so there is no
reason to retype them by hand into this project's own check table.

This reads a NARROW subset of Vale's YAML on purpose, using only the
standard library, because `stopslop.py` is on the gate path and CI proves
that path imports nothing outside stdlib. Anything the subset does not
cover raises `UnsupportedRule` and names what it hit. That is the whole
design: a rule this importer cannot faithfully represent must not be
silently approximated into a check that fires on something else. A
half-understood rule is worse than an absent one, because nothing
downstream ever questions it again.

Supported: `extends: existence` with `tokens` or `raw`, plus `message`,
`level`, `ignorecase`, `nonword`. Everything else -- substitution,
occurrence, conditional, sequence, capitalization, readability, spelling,
consistency, repetition -- is refused by name.
"""
import os
import re

SUPPORTED_EXTENDS = frozenset({"existence"})

# Vale severities to this project's own two actions. Vale's "error" is a
# CI failure, which is the closest thing it has to a blocking gate.
LEVEL_ACTIONS = {"error": "block", "warning": "warn", "suggestion": "warn"}

_SCALARS = ("extends", "message", "level", "ignorecase", "nonword", "scope",
             "link", "description")
_LISTS = ("tokens", "raw")


class UnsupportedRule(Exception):
    """A Vale rule this importer will not guess at."""


class ValeParseError(Exception):
    pass


def _unquote(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
        inner = value[1:-1]
        # YAML single-quote escaping doubles the quote character.
        return inner.replace("''", "'") if value[0] == "'" else inner
    return value


def parse_rule(text, name):
    """One Vale rule file's fields. Deliberately not a YAML parser.

    It reads top-level `key: value` scalars and `key:` followed by `- item`
    lists, which is the entire shape of every existence rule in the wild.
    A construct outside that shape raises rather than being skipped, so an
    unread field can never quietly change what a rule means.
    """
    fields = {}
    current = None
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.lstrip().startswith("- "):
            if current is None:
                raise ValeParseError(f"{name}: list item outside any key")
            fields[current].append(_unquote(line.lstrip()[2:]))
            continue
        if line[0].isspace():
            raise ValeParseError(
                f"{name}: nested mapping is outside this importer's subset "
                f"({line.strip()!r})")
        if ":" not in line:
            raise ValeParseError(f"{name}: cannot read line {line!r}")
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if not value:
            if key not in _LISTS:
                raise UnsupportedRule(
                    f"{name}: block value for {key!r} is outside this "
                    "importer's subset -- import it by hand or extend "
                    "core/vale_import.py")
            fields[key] = []
            current = key
        else:
            if key not in _SCALARS:
                raise UnsupportedRule(f"{name}: unknown field {key!r}")
            fields[key] = _unquote(value)
            current = None
    return fields


def _pattern(fields, name):
    if fields.get("raw"):
        # Vale concatenates raw entries; rules in the wild rely on it by
        # opening later entries with '|'.
        return "".join(fields["raw"])
    tokens = fields.get("tokens")
    if not tokens:
        raise UnsupportedRule(f"{name}: existence rule with neither tokens "
                               "nor raw")
    joined = "|".join(tokens)
    if str(fields.get("nonword", "")).lower() == "true":
        return f"(?:{joined})"
    return rf"\b(?:{joined})\b"


def check_id_for(name, prefix="vale"):
    """`AbstractTriad` -> `vale_abstract_triad`."""
    snake = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
    snake = re.sub(r"[^a-z0-9_]+", "_", snake).strip("_")
    return f"{prefix}_{snake}" if prefix else snake


def _split_message(message):
    """Vale packs catch and remedy into one message, usually around a
    colon. Split it so a flag reads the way every native check reads.
    """
    message = (message or "").replace("%s", "this").strip()
    if ":" in message:
        catches, _, instead = message.partition(":")
        return catches.strip(), instead.strip()
    return message, "rewrite it"


def convert(text, name, prefix="vale"):
    """One Vale rule file to the arguments add_custom_check wants."""
    fields = parse_rule(text, name)
    extends = fields.get("extends")
    if extends is None:
        raise UnsupportedRule(f"{name}: no 'extends' field")
    if extends not in SUPPORTED_EXTENDS:
        raise UnsupportedRule(
            f"{name}: 'extends: {extends}' is not supported -- only "
            f"{', '.join(sorted(SUPPORTED_EXTENDS))}")
    pattern = _pattern(fields, name)
    try:
        re.compile(pattern)
    except re.error as exc:
        raise UnsupportedRule(f"{name}: pattern does not compile: {exc}") from exc
    catches, instead = _split_message(fields.get("message"), )
    level = (fields.get("level") or "suggestion").lower()
    if level not in LEVEL_ACTIONS:
        raise UnsupportedRule(f"{name}: unknown level {level!r}")
    ignorecase = str(fields.get("ignorecase", "")).lower() == "true"
    check_id = check_id_for(name, prefix)
    flags = "re.IGNORECASE" if ignorecase else "0"
    fn_body = (
        f'import re\n'
        f'pattern = re.compile(\n'
        f'    {pattern!r},\n'
        f'    {flags})\n'
        f'match = pattern.search(sentence)\n'
        f'if not match:\n'
        f'    return []\n'
        f'return [{{"phrase": match.group(0), "auto_fix": False,\n'
        f'          "note": {instead!r}}}]\n')
    return {"check_id": check_id, "unit": "sentence", "catches": catches,
            "instead": instead, "threshold": 1,
            "action": LEVEL_ACTIONS[level], "fn_body": fn_body}


def read_package(directory, prefix="vale"):
    """(converted, refused) for every `.yml` in a Vale style directory.

    A refusal is a named pair, never a silent omission, so an import
    reports exactly which of a package's rules did not come across and
    why. A package is rarely all-or-nothing and a partial import that
    hides its own gaps is how a user comes to believe they are covered.
    """
    converted, refused = [], []
    if not os.path.isdir(directory):
        raise FileNotFoundError(f"no Vale style directory at {directory}")
    for filename in sorted(os.listdir(directory)):
        if not filename.endswith((".yml", ".yaml")):
            continue
        name = os.path.splitext(filename)[0]
        with open(os.path.join(directory, filename)) as f:
            text = f.read()
        try:
            converted.append(convert(text, name, prefix))
        except (UnsupportedRule, ValeParseError) as exc:
            refused.append((name, str(exc)))
    return converted, refused
