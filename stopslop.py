#!/usr/bin/env python3
"""stopslop: one entry point for everything a person actually does with
this tool by hand. The gate itself (`src/pretool_hook.py`,
`sessionstart_hook.py`) runs automatically once wired up via Claude Code
hooks and never needs a person to invoke it directly -- this script is for
the parts that do: first-time setup, an ad-hoc compliance check outside a
live write, registering project vocabulary, and checking the tool's own
state.

    stopslop.py init                 wire up .claude/settings.local.json
    stopslop.py lint TEXT            check text without writing it anywhere
    stopslop.py lint --file PATH     check an existing file the same way
    stopslop.py scan [PATH ...]      bulk-check an existing tree of files, no live write
    stopslop.py register WORD [NOTE] add a project-glossary term
    stopslop.py status               dictionary/glossary/gate-activity summary
    stopslop.py list-rulesets        show every registered ruleset and what routes to it

Every command that checks or registers text against a ruleset takes an
optional --ruleset ID. Omit it and the target resolves through the same
config-driven path resolution the live gate uses (`core.config.resolve_ruleset`):
--file PATH resolves against PATH directly; free text/stdin resolves as if
it were being written to a synthetic `<repo_root>/__stdin__.md`, so there's
exactly one resolution mechanism shared by every entry point rather than a
second, separately-maintained default that could quietly drift from it.
"""
import argparse
import json
import os
import subprocess
import sys
import webbrowser

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(REPO_ROOT, "src")
sys.path.insert(0, SRC_DIR)

import dashboard_launch
import rulesets
from core import config as core_config
from core import extract as core_extract
from core import flags as core_flags
from core.version import VERSION

SETTINGS_EXAMPLE = os.path.join(REPO_ROOT, ".claude", "settings.local.json.example")
SETTINGS_REAL = os.path.join(REPO_ROOT, ".claude", "settings.local.json")

# Free text and stdin have no real file path to resolve a ruleset from --
# treated as if written to this synthetic path under the repo root so they
# go through the exact same config-driven resolution a real write would,
# instead of a second "default ruleset" concept that could drift from it.
_SYNTHETIC_STDIN_PATH = os.path.join(REPO_ROOT, core_config.SYNTHETIC_TEXT_NAME)


def _resolve(ruleset_id, target_path):
    """The one resolution mechanism every command below uses: an explicit
    --ruleset always wins; otherwise resolve `target_path` through the same
    config-driven path `core.config.resolve_ruleset` uses for a live write.
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


def _install_git_precommit():
    """Wire `stopslop.py precommit` as the repo's git pre-commit hook.

    The PreToolUse hook guards one harness's tool loop, and only for
    sessions started in this directory. A session working from elsewhere
    by absolute path, a human in an editor, and every clever Bash write
    all reach the repo through ONE shared path: git. Never clobbers a
    pre-commit that is not stopslop's own."""
    hooks_dir = os.path.join(REPO_ROOT, ".git", "hooks")
    if not os.path.isdir(hooks_dir):
        return
    hook_path = os.path.join(hooks_dir, "pre-commit")
    script = ("#!/bin/sh\n# installed by stopslop.py init\n"
              f'exec python3 "{os.path.join(REPO_ROOT, "stopslop.py")}" precommit\n')
    if os.path.exists(hook_path):
        with open(hook_path) as f:
            existing = f.read()
        if "stopslop" not in existing:
            print(f"{hook_path} exists and is not stopslop's; left alone. "
                  f"Add `stopslop.py precommit` to it by hand for the commit gate.")
            return
        if existing == script:
            return
    with open(hook_path, "w") as f:
        f.write(script)
    os.chmod(hook_path, 0o755)
    print(f"Wrote {hook_path} (the commit-time gate; bypass once with --no-verify)")


def _git_show(ref):
    """One git object's text, or None for binary/missing -- either way,
    nothing the gate can judge."""
    import subprocess
    try:
        return subprocess.run(["git", "show", ref], capture_output=True,
                                text=True, check=True, cwd=REPO_ROOT).stdout
    except (subprocess.CalledProcessError, OSError, UnicodeDecodeError):
        return None


def _gate_state(rel, content, full):
    """(blocking, weight) for one file state under its routing, host and
    embedded passes both -- or None when nothing gates it."""
    ruleset = core_config.resolve_ruleset(full, REPO_ROOT, rulesets)
    rule = core_config.matching_rule(full, REPO_ROOT)
    embedded = core_extract.rule_embedded_ruleset(rule, rulesets)
    if ruleset is None and embedded is None:
        return None
    blocking = []
    extension = os.path.splitext(rel)[1]
    if ruleset is not None:
        semantic = ruleset.lint_and_gate(content, file_path=full)["semantic_flags"]
        blocking += ruleset.blocking_semantic_flags(semantic)
    if embedded is not None:
        pool = core_extract.embedded_prose_pool(content, extension, embedded,
                                                  file_path=full)
        blocking += embedded.blocking_semantic_flags(pool)
    # Weight of the POLICY's own output, not of every flag raised -- see
    # the same note in pretool_hook.py's ratchet.
    return blocking, core_flags.flag_weight(blocking)


def cmd_precommit(args):
    """Gate the STAGED tree the way the live hook gates a write: judge
    each staged file's staged content, ratcheted against its HEAD
    version. A commit is refused only for a file that is deniable AND
    carries more flag-occurrences than it did at HEAD, so legacy flags
    never freeze the repo -- the same monotone rule pretool_hook.py
    applies per write, at the one choke point every writer shares."""
    import subprocess
    try:
        staged = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            capture_output=True, text=True, check=True, cwd=REPO_ROOT,
        ).stdout.splitlines()
    except (subprocess.CalledProcessError, OSError):
        return 0    # no git to read: never break a commit path blind
    failures = 0
    for rel in staged:
        full = os.path.join(REPO_ROOT, rel)
        after = _git_show(f":{rel}")
        if after is None:
            continue
        state = _gate_state(rel, after, full)
        if state is None:
            continue
        blocking, after_weight = state
        if not blocking:
            continue
        before = _git_show(f"HEAD:{rel}")
        if before and before.strip():
            before_state = _gate_state(rel, before, full)
            if before_state and after_weight <= before_state[1]:
                continue    # deniable, but no worse than HEAD
            before_weight = before_state[1] if before_state else 0
        else:
            before_weight = 0
        failures += 1
        print(f"stopslop: {rel}: {len(blocking)} blocking flag(s), "
              f"{after_weight} occurrence(s) vs {before_weight} at HEAD")
        for f in blocking[:6]:
            where = f" (line {f['embedded_line']})" if "embedded_line" in f else ""
            print(f"  [{f['kind']}] {core_flags.display_label(f)}{where}")
    if failures:
        print(f"stopslop: commit blocked ({failures} file(s)). Fix the "
              f"additions, or bypass once with `git commit --no-verify`.")
        return 1
    return 0


def _bootstrap_venv(venv_dir, requirements_path, run=subprocess.run):
    """Best-effort: create the venv and install requirements, printing
    progress as it goes. Any failure (no network, no python3-venv package,
    a pip error) prints the exact manual fallback and returns False rather
    than leaving someone stuck with a bare traceback for a step that is
    always allowed to fail -- init's own settings write already succeeded
    by the time this runs, so a failure here must not read as init itself
    having failed. `run` is injectable so tests can verify both branches
    without a real subprocess or network access."""
    venv_python = dashboard_launch.venv_python_path(os.path.dirname(venv_dir))
    print(f"\nSetting up a virtual environment at {venv_dir} "
          f"(for the optional MCP tools and dashboard)...")
    try:
        run([sys.executable, "-m", "venv", venv_dir], check=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"  could not create the venv ({exc}). Set it up by hand:")
        print(f"    python3 -m venv {venv_dir}")
        print(f"    {venv_python} -m pip install -r {requirements_path}")
        return False
    print("Installing requirements (mcp, streamlit)...")
    try:
        run([venv_python, "-m", "pip", "install", "-q", "-r", requirements_path], check=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"  pip install failed ({exc}). Finish it by hand:")
        print(f"    {venv_python} -m pip install -r {requirements_path}")
        return False
    print("Virtual environment ready.")
    return True


def cmd_init(args):
    # Before the settings guard, not after: the commit gate is idempotent
    # and self-guarded, and a repo initialized before it existed should
    # gain it from a plain re-run, not need --force (which is about
    # OVERWRITING settings, an unrelated risk).
    _install_git_precommit()
    if os.path.exists(SETTINGS_REAL) and not args.force:
        print(f"{SETTINGS_REAL} already exists -- not overwriting.")
        print("Re-run with --force if you want to replace it.")
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
    print("The first time you do, Claude Code will ask whether to allow this "
          "project's MCP servers (.mcp.json) -- say yes, or the MCP tools and the dashboard they "
          "auto-start won't connect. Run `stopslop.py status` afterward to confirm "
          "everything is actually wired up.")

    # The gate itself needs nothing beyond the above -- it's stdlib-only.
    # The optional MCP tools (.mcp.json, already checked into this repo)
    # and `stopslop.py dashboard` share one venv, since that's a real
    # dependency, not stdlib. Set up automatically so `init` is the one
    # command that gets everything running -- --no-venv opts back out to
    # the old print-only behavior, for a minimal gate-only install.
    venv_python = dashboard_launch.venv_python_path(REPO_ROOT)
    if not os.path.exists(venv_python):
        if args.no_venv:
            print("\nSkipped venv setup (--no-venv). The MCP convenience tools and "
                  "`stopslop.py dashboard` need one; not required for the gate itself. "
                  "To set one up later:")
            print(f"  python3 -m venv {os.path.join(REPO_ROOT, '.venv')}")
            print(f"  {venv_python} -m pip install -r {os.path.join(REPO_ROOT, 'requirements.txt')}")
        else:
            _bootstrap_venv(os.path.join(REPO_ROOT, ".venv"),
                             os.path.join(REPO_ROOT, "requirements.txt"))

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
    result = ruleset.lint_and_gate(text, context=args.context, file_path=target_path)
    mechanical = result["mechanical_violations"]
    # Same filter the live gate applies (ruleset.blocking_semantic_flags) --
    # this command reports what a real write would actually do, not every
    # flag the engine can produce. The full, unfiltered set is available
    # with --all.
    blocking = ruleset.blocking_semantic_flags(result["semantic_flags"])
    excluded_count = len(result["semantic_flags"]) - len(blocking)
    semantic = result["semantic_flags"] if args.all else blocking

    # The embedded-prose pass a real write would also run -- skipped when
    # --ruleset overrides resolution, which means "lint as exactly this
    # ruleset and nothing else". See core/extract.py.
    embedded_blocking, embedded_module = [], None
    if not args.ruleset:
        rule = core_config.matching_rule(target_path, REPO_ROOT)
        embedded_module = core_extract.rule_embedded_ruleset(rule, rulesets)
        if embedded_module is not None:
            embedded_blocking = core_extract.embedded_prose_flags(
                text, os.path.splitext(target_path)[1], embedded_module,
                file_path=target_path)

    print(f"[{ruleset.RULESET_NAME}]")
    if not mechanical and not semantic and not embedded_blocking:
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

    if embedded_blocking:
        print(f"Embedded prose ({embedded_module.RULESET_NAME}): "
              f"{len(embedded_blocking)} blocking flag(s) -- a real write "
              f"would be denied:\n")
        for f in embedded_blocking:
            label = f.get("label") or f["detail"].get("rule", "?")
            # A document-level check (em_dash_cluster) has no single
            # sentence of its own to attribute a line to -- see
            # core/extract.py's embedded_prose_pool docstring. Printing
            # nothing there beats a KeyError from assuming every flag
            # carries one.
            where = f"line {f['embedded_line']}: " if "embedded_line" in f else ""
            print(f"  {where}[{f['kind']}] {label!r}")
        print()

    return 1 if (semantic or embedded_blocking) else 0


def cmd_scan(args):
    from core import scan as core_scan

    if args.glob != "*" and not args.ruleset:
        print("--glob only applies together with --ruleset (config-driven resolution "
              "already narrows file selection by its own routing globs).", file=sys.stderr)
        return 1

    target_paths = [os.path.abspath(p) for p in args.paths] if args.paths else [REPO_ROOT]
    for p in target_paths:
        if not os.path.exists(p):
            print(f"{p!r} does not exist.", file=sys.stderr)
            return 1

    if args.ruleset:
        rulesets.get_ruleset(args.ruleset)  # raises UnknownRulesetError on a typo, loud on purpose

    report = core_scan.scan_tree(target_paths, REPO_ROOT, rulesets,
                                  ruleset_id=args.ruleset, glob_pattern=args.glob)

    if args.json:
        print(json.dumps(report, indent=2, default=str))
        return 1 if any(r["would_block"] for r in report["results"]) else 0

    fail = [r for r in report["results"] if r["would_block"]]
    with_notes = [r for r in report["results"]
                  if not r["would_block"] and (r["mechanical_flags"] or r["all_semantic_flags"])]
    clean_count = report["scanned"] - len(fail) - len(with_notes)

    if not args.quiet:
        for r in fail + with_notes:
            status = "FAIL" if r["would_block"] else "PASS"
            rel = os.path.relpath(r["path"], REPO_ROOT)
            n_blocking = len(r["blocking_flags"])
            n_mech = len(r["mechanical_flags"])
            n_notes = len(r["all_semantic_flags"]) - n_blocking
            bits = []
            if n_blocking:
                bits.append(f"{n_blocking} blocking issue(s)")
            if n_mech:
                bits.append(f"{n_mech} mechanical fix(es)")
            if n_notes and args.all:
                bits.append(f"{n_notes} non-blocking note(s)")
            print(f"{status}  {rel} [{r['ruleset']}]  " + ", ".join(bits))
            if args.all:
                for f in r["all_semantic_flags"]:
                    d = f["detail"]
                    label = f.get("label") or d.get("rule", "?")
                    note = d.get("note") or d.get("basis") or ""
                    extra = f" -- {note}" if note else ""
                    print(f"    [{f['kind']}, rule {d.get('rule', '?')}] {label!r}{extra}")
                for m in r["mechanical_flags"]:
                    d = m["detail"]
                    label = m.get("label") or d.get("rule", "?")
                    repl = d.get("replacement")
                    arrow = f" -> {repl!r}" if repl else ""
                    print(f"    [{m['kind']}, auto-fix] {label!r}{arrow}")
        print()

    kind_counts = {}
    for r in report["results"]:
        for f in r["all_semantic_flags"] + r["mechanical_flags"]:
            kind_counts[f["kind"]] = kind_counts.get(f["kind"], 0) + 1

    print(f"Scanned {report['scanned']} file(s) "
          f"({report['skipped_out_of_scope']} out of scope, "
          f"{report['skipped_unreadable']} unreadable/binary, skipped).")
    print(f"  {clean_count} clean")
    print(f"  {len(with_notes)} pass, with an auto-fixable mechanical issue and/or "
          f"a non-blocking note")
    print(f"  {len(fail)} would FAIL a live write (need a person's judgment)")
    if kind_counts:
        print("\nBy check, across every flag found:")
        for kind, count in sorted(kind_counts.items(), key=lambda kv: -kv[1]):
            print(f"  {kind}: {count}")

    return 1 if fail else 0


def _require_terms(ruleset):
    if "terms" not in ruleset.CAPABILITIES:
        print(f"'{ruleset.RULESET_ID}' ruleset has no term lists "
              f"(capabilities: {sorted(ruleset.CAPABILITIES)}).", file=sys.stderr)
        sys.exit(1)


def _print_term_list(list_id, view):
    arrow = "allowed" if view["polarity"] == "allow" else "flagged"
    print(f"{list_id} [{view['polarity']}: matching terms are {arrow}] -- {view['label']}")
    layers = [f"{view['built_in_count']} built-in"]
    if view["accepts_packs"]:
        layers.append(f"{view['pack_count']} from packs")
    layers.append(f"{view['project_count']} yours")
    if view.get("suppressed_count"):
        layers.append(f"{view['suppressed_count']} suppressed")
    print(f"  {view['effective_count']} effective ({', '.join(layers)})")
    for term, info in sorted(view["project_terms"].items()):
        flag = " [overrides a real prohibition]" if info.get("overrides_unapproved") else ""
        note = info.get("note", "")
        print(f"    {term}{flag}" + (f" -- {note}" if note else ""))
    if view["rejected"]:
        print(f"  {len(view['rejected'])} pack term(s) refused by this ruleset's own "
              f"prohibitions: {', '.join(sorted(view['rejected'])[:8])}")


def cmd_terms(args):
    """One command for every named word list any ruleset owns.

    Replaces five: register, unregister, terms, glossary-packs and
    wordlist. They existed separately because ste100's allow list and
    slopwatch's deny lists were modelled as different concepts -- see
    src/core/terms.py for why they never were."""
    ruleset = _resolve(args.ruleset, _SYNTHETIC_STDIN_PATH)
    _require_terms(ruleset)

    if args.add is not None:
        if not args.list:
            print(f"`--add` needs `--list LIST_ID` -- known: "
                  f"{sorted(ruleset.list_term_lists())}", file=sys.stderr)
            return 1
        try:
            result = ruleset.add_term(args.list, args.add, args.note or "",
                                       force=args.force or False)
        except Exception as exc:
            print(f"Not saved: {exc}", file=sys.stderr)
            return 1
        stream = sys.stdout if result.get("ok") else sys.stderr
        print(result.get("message", ""), file=stream)
        if not result.get("ok"):
            return 1

    if args.remove is not None:
        if not args.list:
            print(f"`--remove` needs `--list LIST_ID` -- known: "
                  f"{sorted(ruleset.list_term_lists())}", file=sys.stderr)
            return 1
        try:
            result = ruleset.remove_term(args.list, args.remove)
        except Exception as exc:
            print(f"Not saved: {exc}", file=sys.stderr)
            return 1
        print(result.get("message", ""))

    views = ruleset.list_term_lists()
    if args.list and args.list not in views:
        print(f"Not found: unknown list {args.list!r} -- known: {sorted(views)}",
              file=sys.stderr)
        return 1
    for list_id in ([args.list] if args.list else sorted(views)):
        _print_term_list(list_id, views[list_id])
    return 0


def cmd_packs(args):
    """Vocabulary packs. A pack is inert content from a real source; where
    it applies (a path glob) and what it feeds (a term list) are both
    project decisions, made here, not baked into the pack."""
    from core import glossary_packs

    if args.enable is not None:
        if not args.glob or not args.list:
            print("`--enable` needs `--glob GLOB` and `--list LIST_ID`: a pack "
                  "applies to a path, and feeds one named term list.", file=sys.stderr)
            return 1
        try:
            core_config.set_rule_packs(REPO_ROOT, args.glob, args.list, args.enable,
                                        known_packs=glossary_packs.AVAILABLE_PACKS)
        except Exception as exc:
            print(f"Not saved: {exc}", file=sys.stderr)
            return 1
        print(f"{args.glob} -> {args.list}: {', '.join(args.enable) or '(none)'}")

    print("Available packs (any of these can feed any term list):")
    for pack_id, meta in sorted(glossary_packs.list_packs().items()):
        print(f"  {pack_id} -- {meta['name']} "
              f"({meta['license']}, {meta['term_count']} term(s))")
        print(f"      {meta['source']}")

    print("\nEnabled per routing rule:")
    any_enabled = False
    for glob, ruleset_id, by_list in core_config.rule_packs(REPO_ROOT):
        for list_id, pack_ids in sorted(by_list.items()):
            if pack_ids:
                any_enabled = True
                print(f"  {glob} [{ruleset_id}] -> {list_id}: {', '.join(pack_ids)}")
    if not any_enabled:
        print("  (none)")
    return 0


def _parse_check_id_value(item, value_kind, valid_values=None):
    """CHECK_ID=VALUE -> (check_id, value), or None with a printed error.
    Shared by --set-threshold (an int) and --set-action (one of a closed
    set) -- one KEY=VALUE shape across the checks command."""
    if "=" not in item:
        print(f"Not saved: {item!r} isn't in CHECK_ID=VALUE form.", file=sys.stderr)
        return None
    check_id, raw_value = item.split("=", 1)
    if value_kind is int:
        try:
            return check_id, int(raw_value)
        except ValueError:
            print(f"Not saved: {raw_value!r} isn't a whole number for {check_id!r}.",
                  file=sys.stderr)
            return None
    if raw_value not in valid_values:
        print(f"Not saved: {raw_value!r} isn't one of {sorted(valid_values)} for {check_id!r}.",
              file=sys.stderr)
        return None
    return check_id, raw_value


def cmd_checks(args):
    ruleset = _resolve(args.ruleset, _SYNTHETIC_STDIN_PATH)
    if not hasattr(ruleset, "list_checks"):
        print(f"'{ruleset.RULESET_ID}' ruleset has no individually-toggleable checks.",
              file=sys.stderr)
        return 1

    if args.enable is not None:
        try:
            ruleset.set_enabled_checks(args.enable)
        except Exception as exc:
            print(f"Not saved: {exc}", file=sys.stderr)
            return 1
        print(f"Enabled: {', '.join(sorted(args.enable)) or '(none)'}")

    has_check_config = "check_config" in ruleset.CAPABILITIES
    if not has_check_config and (args.set_threshold or args.set_action or args.set_param):
        print(f"'{ruleset.RULESET_ID}' ruleset has no per-check threshold/action to set.",
              file=sys.stderr)
        return 1
    for item in args.set_threshold or []:
        parsed = _parse_check_id_value(item, int)
        if not parsed:
            return 1
        check_id, threshold = parsed
        try:
            ruleset.set_check_config(check_id, threshold=threshold)
        except Exception as exc:
            print(f"Not saved: {exc}", file=sys.stderr)
            return 1
        print(f"Set {check_id} threshold={threshold}")
    for item in args.set_action or []:
        parsed = _parse_check_id_value(item, str, valid_values={"block", "warn"})
        if not parsed:
            return 1
        check_id, action = parsed
        try:
            ruleset.set_check_config(check_id, action=action)
        except Exception as exc:
            print(f"Not saved: {exc}", file=sys.stderr)
            return 1
        print(f"Set {check_id} action={action}")
    for item in args.set_param or []:
        # CHECK_ID.PARAM=N -- a check's own extra number, e.g.
        # length.procedure_word_limit=20. Only checks that declare the
        # param accept it; set_check_config validates and says which.
        if "=" not in item or "." not in item.split("=", 1)[0]:
            print(f"Not saved: {item!r} isn't in CHECK_ID.PARAM=N form.",
                  file=sys.stderr)
            return 1
        target, raw_value = item.split("=", 1)
        check_id, param = target.split(".", 1)
        try:
            value = int(raw_value)
        except ValueError:
            print(f"Not saved: {raw_value!r} isn't a whole number for {target!r}.",
                  file=sys.stderr)
            return 1
        try:
            ruleset.set_check_config(check_id, **{param: value})
        except Exception as exc:
            print(f"Not saved: {exc}", file=sys.stderr)
            return 1
        print(f"Set {check_id} {param}={value}")

    check_config = ruleset.list_check_config() if has_check_config else {}
    for check_id, meta in sorted(ruleset.list_checks().items()):
        state = "ON " if meta["enabled"] else "off"
        tuning = ""
        if check_id in check_config:
            spec = check_config[check_id]
            tuning = f" (threshold={spec['threshold']}, action={spec['action']})"
            params = spec.get("params", {})
            if params:
                tuning = tuning[:-1] + ", " + ", ".join(
                    f"{n}={i['value']}" for n, i in sorted(params.items())) + ")"
        print(f"[{state}] {check_id}{tuning} -- {meta['catches']}")
        if meta["instead"]:
            print(f"{'':<7} instead: {meta['instead']}")
    return 0


def cmd_status(args):
    import status_report
    if args.clean_config:
        stray = core_config.stray_top_level_keys(REPO_ROOT)
        if not stray:
            print("No stray config keys to remove.")
        else:
            core_config.strip_top_level_keys(REPO_ROOT, stray)
            print(f"Removed: {', '.join(stray)}")
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
    venv_python = dashboard_launch.venv_python_path(REPO_ROOT)
    if not os.path.exists(venv_python):
        print(
            "stopslop dashboard: no virtual environment at .venv -- it needs one, "
            "the same as the MCP tools. Set it up, then re-run this command:\n"
            f"  python3 -m venv {os.path.join(REPO_ROOT, '.venv')}\n"
            f"  {venv_python} -m pip install -r {os.path.join(REPO_ROOT, 'requirements.txt')}",
            file=sys.stderr,
        )
        return 1
    # An MCP session may have already auto-started this (see
    # dashboard_launch.py) -- re-execing streamlit into an occupied port
    # would just crash on bind, so point the browser at the live one
    # instead of trying to start a second, competing copy.
    if dashboard_launch.is_alive():
        url = dashboard_launch.dashboard_url()
        print(f"stopslop dashboard: already running at {url}")
        webbrowser.open(url)
        return 0
    argv = dashboard_launch.streamlit_argv(
        venv_python, dashboard_launch.dashboard_path(),
        dashboard_launch.DASHBOARD_PORT, headless=False)
    os.execv(venv_python, argv)


def main():
    parser = argparse.ArgumentParser(
        prog="stopslop.py",
        description="stopslop: a pluggable writing-enforcement gate for Claude Code. "
                     "The gate runs automatically once `init` has wired it up; "
                     "these commands are for everything else a person does by hand.")
    parser.add_argument("--version", action="version", version=f"stopslop {VERSION}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="wire up .claude/settings.local.json for this clone, "
                                          "and set up the venv the MCP tools/dashboard need")
    p_init.add_argument("--force", action="store_true", help="overwrite an existing settings file")
    p_init.add_argument("--no-venv", action="store_true",
                         help="skip auto-installing the optional MCP/dashboard virtual environment")
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

    p_scan = sub.add_parser("scan", help="bulk-check an existing tree of files against a ruleset, "
                                          "with no live write -- for adopting stopslop onto a "
                                          "codebase that already exists, not just files edited going forward")
    p_scan.add_argument("paths", nargs="*", help="file(s)/directory(ies) to scan (default: this project's whole tree)")
    p_scan.add_argument("--ruleset", help="force every matched file through this one ruleset id, "
                                           "ignoring stopslop.config.json's routing (default: resolve "
                                           "each file's ruleset from config, same as a live write -- "
                                           "skips anything out of scope)")
    p_scan.add_argument("--glob", default="*", help="filename pattern to include, only used together "
                                                      "with --ruleset (default: every regular file)")
    p_scan.add_argument("--all", action="store_true", help="show every flag per file, including "
                                                             "non-blocking notes (default: one summary "
                                                             "line per flagged file)")
    p_scan.add_argument("--quiet", action="store_true", help="print only the final summary, no per-file lines")
    p_scan.add_argument("--json", action="store_true", help="machine-readable output instead of the text report")
    p_scan.set_defaults(func=cmd_scan)

    p_terms = sub.add_parser("terms",
                              help="list/extend any ruleset's term lists (replaces "
                                    "register, unregister, terms, glossary-packs, wordlist)")
    p_terms.add_argument("--ruleset", help="ruleset id (default: resolved from config)")
    p_terms.add_argument("--list", metavar="LIST_ID",
                          help="which term list to show or change (no-argument output "
                               "shows the known ids)")
    p_terms.add_argument("--add", metavar="TERM", help="add a term to --list")
    p_terms.add_argument("--note", help="why the term was added -- goes on the record")
    p_terms.add_argument("--remove", metavar="TERM", help="remove a term from --list")
    p_terms.add_argument("--force", metavar="REASON", nargs="?", const=True, default=None,
                          help="register even if the ruleset's own standard forbids the "
                               "word (ste100 requires a REASON; it goes in the note)")
    p_terms.set_defaults(func=cmd_terms)

    p_packs = sub.add_parser("packs",
                              help="list vocabulary packs and attach them to a path glob")
    p_packs.add_argument("--glob", metavar="GLOB",
                          help="which routing rule to change (a pack applies to a PATH, "
                               "not to a ruleset)")
    p_packs.add_argument("--list", metavar="LIST_ID",
                          help="which term list the packs feed (a pack has no opinion "
                               "about that -- see `stopslop.py terms` for the ids)")
    p_packs.add_argument("--enable", nargs="*", metavar="PACK_ID",
                          help="set exactly this list of packs on --glob; pass with no "
                               "ids to disable all of them there")
    p_packs.set_defaults(func=cmd_packs)

    p_pre = sub.add_parser("precommit",
                            help="gate staged files (the git pre-commit hook target)")
    p_pre.set_defaults(func=cmd_precommit)

    p_checks = sub.add_parser("checks", help="list checks for a ruleset, turn them on and off, "
                                              "and tune each one's own threshold/action")
    p_checks.add_argument("--ruleset", help="ruleset id (default: ste100)")
    p_checks.add_argument("--enable", nargs="*", metavar="CHECK_ID",
                           help="set exactly this list of checks as enabled (disables every "
                                "other known check); pass with no ids to disable all")
    p_checks.add_argument("--set-threshold", nargs="+", metavar="CHECK_ID=N",
                           help="how many times a check has to fire in a document before it "
                                "counts as triggered (rulesets with per-check config only)")
    p_checks.add_argument("--set-action", nargs="+", metavar="CHECK_ID=block|warn",
                           help="whether a triggered check denies the write on its own "
                                "(block) or is only shown (warn)")
    p_checks.add_argument("--set-param", nargs="+", metavar="CHECK_ID.PARAM=N",
                           help="a check's own extra number, e.g. "
                                "length.procedure_word_limit=20 (ste100)")
    p_checks.set_defaults(func=cmd_checks)


    p_status = sub.add_parser("status", help="per-ruleset stats and gate-activity summary")
    p_status.add_argument("--clean-config", action="store_true",
                           help="remove stopslop.config.json top-level keys no reader "
                                "consumes anymore (left over from a removed feature), "
                                "before printing the report")
    p_status.set_defaults(func=cmd_status)

    p_list_rulesets = sub.add_parser("list-rulesets", help="show every registered ruleset and what routes to it")
    p_list_rulesets.set_defaults(func=cmd_list_rulesets)

    p_dashboard = sub.add_parser("dashboard", help="open the live web dashboard (needs the venv)")
    p_dashboard.set_defaults(func=cmd_dashboard)

    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
