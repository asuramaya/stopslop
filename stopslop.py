#!/usr/bin/env python3
"""stopslop: one entry point for everything a person actually does with
this tool by hand. The gate itself (src/pretool_hook.py,
sessionstart_hook.py) runs automatically once wired up via Claude Code
hooks and never needs a person to invoke it directly -- this script is for
the parts that do: first-time setup, an ad-hoc compliance check outside a
live write, registering project vocabulary, and checking the tool's own
state.

    stopslop.py init                 wire up .claude/settings.local.json
    stopslop.py lint TEXT            check text without writing it anywhere
    stopslop.py lint --file PATH     check an existing file the same way
    stopslop.py register WORD [NOTE] add a project-glossary term
    stopslop.py status               dictionary/glossary/gate-activity summary
    stopslop.py list-rulesets        show every registered ruleset and what routes to it

Every command that checks or registers text against a ruleset takes an
optional --ruleset ID. Omit it and the target resolves through the same
config-driven path resolution the live gate uses (core.config.resolve_ruleset):
--file PATH resolves against PATH directly; free text/stdin resolves as if
it were being written to a synthetic <repo_root>/__stdin__.md, so there's
exactly one resolution mechanism shared by every entry point rather than a
second, separately-maintained default that could quietly drift from it.
"""
import argparse
import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(REPO_ROOT, "src")
sys.path.insert(0, SRC_DIR)

import rulesets
from core import config as core_config
from core.version import VERSION

SETTINGS_EXAMPLE = os.path.join(REPO_ROOT, ".claude", "settings.local.json.example")
SETTINGS_REAL = os.path.join(REPO_ROOT, ".claude", "settings.local.json")

# Free text and stdin have no real file path to resolve a ruleset from --
# treated as if written to this synthetic path under the repo root so they
# go through the exact same config-driven resolution a real write would,
# instead of a second "default ruleset" concept that could drift from it.
_SYNTHETIC_STDIN_PATH = os.path.join(REPO_ROOT, "__stdin__.md")


def _resolve(ruleset_id, target_path):
    """The one resolution mechanism every command below uses: an explicit
    --ruleset always wins; otherwise resolve target_path through the same
    config-driven path core.config.resolve_ruleset uses for a live write.
    Exits with a clear message (not a traceback) if resolution fails --
    both an unknown --ruleset id and a stopslop.config.json rule naming an
    unregistered id raise loudly by design (see core/config.py)."""
    if ruleset_id:
        return rulesets.get_ruleset(ruleset_id)
    resolved = core_config.resolve_ruleset(target_path, REPO_ROOT, rulesets)
    if resolved is None:
        print(f"{target_path!r} doesn't resolve to any ruleset under the current "
              f"config -- pass --ruleset explicitly, or check stopslop.config.json.",
              file=sys.stderr)
        sys.exit(1)
    return resolved


def cmd_init(args):
    if os.path.exists(SETTINGS_REAL) and not args.force:
        print(f"{SETTINGS_REAL} already exists -- not overwriting.")
        print("Re-run with --force if you really want to replace it.")
        return 1

    with open(SETTINGS_EXAMPLE) as f:
        settings = json.load(f)

    # The example ships with a placeholder path; substitute this actual
    # clone's location so nobody has to hand-edit JSON to get started.
    pretool_path = os.path.join(SRC_DIR, "pretool_hook.py")
    sessionstart_path = os.path.join(SRC_DIR, "sessionstart_hook.py")
    settings["hooks"]["PreToolUse"][0]["hooks"][0]["command"] = f"python3 {pretool_path}"
    settings["hooks"]["SessionStart"][0]["hooks"][0]["command"] = f"python3 {sessionstart_path}"

    # Preserve any top-level key the real file already has that this
    # template doesn't know about -- Claude Code itself writes
    # "enabledMcpjsonServers" here the first time a user approves the MCP
    # server, and a blind overwrite would silently drop it.
    if os.path.exists(SETTINGS_REAL):
        with open(SETTINGS_REAL) as f:
            existing = json.load(f)
        for key, value in existing.items():
            settings.setdefault(key, value)

    os.makedirs(os.path.dirname(SETTINGS_REAL), exist_ok=True)
    with open(SETTINGS_REAL, "w") as f:
        json.dump(settings, f, indent=2)
        f.write("\n")
    print(f"Wrote {SETTINGS_REAL}")
    print("Start (or restart) a Claude Code session in this directory to pick it up.")

    # The gate itself needs nothing beyond the above -- it's stdlib-only.
    # The optional MCP tools (.mcp.json, already checked into this repo)
    # and `stopslop.py dashboard` share one venv, since that's a real
    # dependency, not stdlib.
    venv_python = os.path.join(REPO_ROOT, ".venv", "bin", "python3")
    if not os.path.exists(venv_python):
        print("\nOptional: the MCP convenience tools (.mcp.json) and `stopslop.py dashboard` "
              "need a venv. Not required for the gate itself. To set one up:")
        print(f"  python3 -m venv {os.path.join(REPO_ROOT, '.venv')}")
        print(f"  {venv_python} -m pip install -r {os.path.join(REPO_ROOT, 'requirements.txt')}")

    if not os.path.exists(core_config.config_path(REPO_ROOT)):
        print(f"\nOptional: {core_config.config_path(REPO_ROOT)} controls which ruleset lints "
              f"which files. Not required -- with no config file, .md/.txt/.rst under this "
              f"project lint against ste100 (see stopslop.config.json.example).")
    return 0


def cmd_lint(args):
    if args.file:
        with open(args.file) as f:
            text = f.read()
        target_path = os.path.abspath(args.file)
    elif args.text:
        text = " ".join(args.text)
        target_path = _SYNTHETIC_STDIN_PATH
    else:
        text = sys.stdin.read()
        target_path = _SYNTHETIC_STDIN_PATH

    if not text.strip():
        print("Nothing to check.", file=sys.stderr)
        return 1

    ruleset = _resolve(args.ruleset, target_path)
    result = ruleset.lint_and_gate(text, context=args.context)
    mechanical = result["mechanical_violations"]
    # Same filter the live gate applies (ruleset.blocking_semantic_flags) --
    # this command reports what a real write would actually do, not every
    # flag the engine can produce. The full, unfiltered set is available
    # with --all.
    blocking = ruleset.blocking_semantic_flags(result["semantic_flags"])
    excluded_count = len(result["semantic_flags"]) - len(blocking)
    semantic = result["semantic_flags"] if args.all else blocking

    print(f"[{ruleset.RULESET_NAME}]")
    if not mechanical and not semantic:
        if excluded_count and not args.all:
            # Generic on purpose: what's hidden isn't always a "vocabulary"
            # concept (ste100's is; slopwatch's below-threshold flags are a
            # density judgment, not a vocabulary exclusion) -- an earlier
            # version of this message hardcoded "vocabulary note(s)",
            # copied straight from ste100's own wording, and was actively
            # misleading the first time it printed for a different ruleset.
            print(f"PASS -- would go through the live gate unchanged "
                  f"({excluded_count} non-blocking note(s) hidden, see --all).")
        else:
            print("PASS -- clean, no violations.")
        return 0

    if semantic:
        print(f"FAIL -- {len(semantic)} issue(s) need a person's judgment:\n")
        for f in semantic:
            d = f["detail"]
            label = f.get("label") or d.get("rule", "?")
            rule = d.get("rule", "?")
            note = d.get("note") or d.get("basis") or ""
            extra = f" -- {note}" if note else ""
            print(f"  [{f['kind']}, rule {rule}] {label!r}{extra}")
        print()

    if mechanical:
        print(f"{len(mechanical)} mechanical fix(es) would be applied automatically on a real write:\n")
        for m in mechanical:
            d = m["detail"]
            label = m.get("label") or d.get("rule", "?")
            repl = d.get("replacement")
            arrow = f" -> {repl!r}" if repl else ""
            print(f"  [{m['kind']}] {label!r}{arrow}")

    return 1 if semantic else 0


def _require_glossary(ruleset, verb):
    if "glossary" not in ruleset.CAPABILITIES:
        print(f"'{ruleset.RULESET_ID}' ruleset has no glossary/vocabulary registry "
              f"(capabilities: {sorted(ruleset.CAPABILITIES)}) -- nothing to {verb} here.",
              file=sys.stderr)
        sys.exit(1)


def cmd_register(args):
    parser = argparse.ArgumentParser(prog="stopslop.py register", add_help=False)
    parser.add_argument("word")
    parser.add_argument("note", nargs="?", default="")
    parser.add_argument("--override-unapproved", metavar="REASON", default=None)
    sub_args = parser.parse_args(args.rest)

    ruleset = _resolve(args.ruleset, _SYNTHETIC_STDIN_PATH)
    _require_glossary(ruleset, "register")
    result = ruleset.register_term(sub_args.word, sub_args.note, sub_args.override_unapproved)
    stream = sys.stdout if result["status"] == "registered" else sys.stderr
    prefix = "" if result["status"] == "registered" else f"{result['status']}: "
    print(f"{prefix}{result['message']}", file=stream)
    return 0 if result["ok"] else 1


def cmd_unregister(args):
    ruleset = _resolve(args.ruleset, _SYNTHETIC_STDIN_PATH)
    _require_glossary(ruleset, "unregister")
    result = ruleset.unregister_term(args.word)
    print(result["message"])
    return 0 if result["ok"] else 1


def cmd_terms(args):
    ruleset = _resolve(args.ruleset, _SYNTHETIC_STDIN_PATH)
    _require_glossary(ruleset, "list")
    terms = ruleset.list_terms()
    if not terms:
        print("No project terms registered yet. Add one with `stopslop.py register`.")
        return 0
    for word in sorted(terms):
        info = terms[word]
        flag = " [overrides a real prohibition]" if info.get("overrides_unapproved") else ""
        note = info.get("note", "")
        print(f"{word}{flag}" + (f" -- {note}" if note else ""))
    return 0


def cmd_glossary_packs(args):
    ruleset = _resolve(args.ruleset, _SYNTHETIC_STDIN_PATH)
    if not hasattr(ruleset, "list_glossary_packs"):
        print(f"'{ruleset.RULESET_ID}' ruleset has no vocabulary-pack support.", file=sys.stderr)
        return 1

    if args.enable is not None:
        try:
            ruleset.set_enabled_glossary_packs(args.enable)
        except Exception as exc:
            print(f"Not saved: {exc}", file=sys.stderr)
            return 1
        print(f"Enabled: {', '.join(args.enable) or '(none)'}")

    for pack_id, meta in ruleset.list_glossary_packs().items():
        state = "ON " if meta["enabled"] else "off"
        print(f"[{state}] {pack_id} -- {meta['name']} ({meta['license']}, "
              f"{meta['term_count']} term(s)) -- {meta['source']}")
    return 0


def cmd_status(args):
    import status_report
    print(status_report.format_status_report(status_report.build_status_report()))
    return 0


def cmd_list_rulesets(args):
    rules = core_config.load_rules(REPO_ROOT)
    for ruleset in rulesets.list_rulesets():
        globs = [r["glob"] for r in rules if r.get("ruleset") == ruleset.RULESET_ID]
        print(f"{ruleset.RULESET_ID} -- {ruleset.RULESET_NAME} "
              f"(capabilities: {', '.join(sorted(ruleset.CAPABILITIES)) or 'none'})")
        print(f"  routed globs: {', '.join(globs) if globs else '(none in the current config)'}")
    return 0


def cmd_dashboard(args):
    # Same "clear stderr message instead of an opaque exec failure" pattern
    # mcp_launch.py already established -- see that file's own docstring.
    venv_streamlit = os.path.join(REPO_ROOT, ".venv", "bin", "streamlit")
    if not os.path.exists(venv_streamlit):
        venv_python = os.path.join(REPO_ROOT, ".venv", "bin", "python3")
        print(
            "stopslop dashboard: no virtual environment at .venv -- it needs one, "
            "the same as the MCP tools. Set it up, then re-run this command:\n"
            f"  python3 -m venv {os.path.join(REPO_ROOT, '.venv')}\n"
            f"  {venv_python} -m pip install -r {os.path.join(REPO_ROOT, 'requirements.txt')}",
            file=sys.stderr,
        )
        return 1
    dashboard_path = os.path.join(SRC_DIR, "dashboard.py")
    os.execv(venv_streamlit, [venv_streamlit, "run", dashboard_path])


def main():
    parser = argparse.ArgumentParser(
        prog="stopslop.py",
        description="stopslop: a pluggable writing-enforcement gate for Claude Code. "
                     "The gate runs automatically once `init` has wired it up; "
                     "these commands are for everything else a person does by hand.")
    parser.add_argument("--version", action="version", version=f"stopslop {VERSION}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="wire up .claude/settings.local.json for this clone")
    p_init.add_argument("--force", action="store_true", help="overwrite an existing settings file")
    p_init.set_defaults(func=cmd_init)

    p_lint = sub.add_parser("lint", help="check text or a file without writing it anywhere")
    p_lint.add_argument("text", nargs="*", help="text to check (omit to read a file or stdin instead)")
    p_lint.add_argument("--file", help="check an existing file's content instead of inline text")
    p_lint.add_argument("--ruleset", help="ruleset id to check against (default: resolved from "
                                           "--file's path, or stopslop.config.json's default rule)")
    p_lint.add_argument("--context", default="description",
                         help="passed through to the resolved ruleset -- for ste100: "
                              "procedure (20-word limit, step-by-step instructions) or "
                              "description (25-word limit, default, whole documents)")
    p_lint.add_argument("--all", action="store_true",
                         help="show every flag the engine produces, including notes "
                              "the live gate doesn't currently act on (see README's gap list)")
    p_lint.set_defaults(func=cmd_lint)

    p_register = sub.add_parser("register", help="add a word to a ruleset's glossary, if it has one",
                                 add_help=False)
    p_register.add_argument("--ruleset", help="ruleset id to register against (default: ste100)")
    p_register.add_argument("rest", nargs=argparse.REMAINDER,
                             help="WORD [NOTE] [--override-unapproved REASON]")
    p_register.set_defaults(func=cmd_register)

    p_unregister = sub.add_parser("unregister", help="remove a word from a ruleset's glossary")
    p_unregister.add_argument("--ruleset", help="ruleset id (default: ste100)")
    p_unregister.add_argument("word")
    p_unregister.set_defaults(func=cmd_unregister)

    p_terms = sub.add_parser("terms", help="list every registered glossary word for a ruleset")
    p_terms.add_argument("--ruleset", help="ruleset id (default: ste100)")
    p_terms.set_defaults(func=cmd_terms)

    p_packs = sub.add_parser("glossary-packs", help="list/enable bulk vocabulary packs for a ruleset")
    p_packs.add_argument("--ruleset", help="ruleset id (default: ste100)")
    p_packs.add_argument("--enable", nargs="*", metavar="PACK_ID",
                          help="set exactly this list of packs as enabled (disables every "
                               "other known pack); pass with no ids to disable all")
    p_packs.set_defaults(func=cmd_glossary_packs)

    p_status = sub.add_parser("status", help="per-ruleset stats and gate-activity summary")
    p_status.set_defaults(func=cmd_status)

    p_list_rulesets = sub.add_parser("list-rulesets", help="show every registered ruleset and what routes to it")
    p_list_rulesets.set_defaults(func=cmd_list_rulesets)

    p_dashboard = sub.add_parser("dashboard", help="open the live web dashboard (needs the venv)")
    p_dashboard.set_defaults(func=cmd_dashboard)

    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
