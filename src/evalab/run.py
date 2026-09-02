#!/usr/bin/env python3
"""Command line for the A/B harness.

    python3 src/evalab/run.py --live --out evalab-runs/2026-09-01
    python3 src/evalab/run.py --replay evalab-runs/2026-09-01/recordings

--live costs real tokens: two arms per prompt, and the gated arm
generates again on every revision, so budget prompts x (1 + iterations)
calls. It records every call, so the same run replays for free
afterwards.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import rulesets
from evalab import harness, prompts as prompt_set, report
from evalab.generators import ClaudeCliGenerator, GeneratorError, RecordedGenerator


def _save(out_dir, result):
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "result.json"), "w") as f:
        json.dump(result, f, indent=1)
        f.write("\n")
    text_dir = os.path.join(out_dir, "texts")
    os.makedirs(text_dir, exist_ok=True)
    for row in result["rows"]:
        for arm in ("ungated", "instructed", "gated"):
            if arm not in row:
                continue
            with open(os.path.join(text_dir, f"{row['id']}.{arm}.md"), "w") as f:
                f.write(row[arm]["text"].rstrip() + "\n")
    rendered = report.render(result)
    with open(os.path.join(out_dir, "report.txt"), "w") as f:
        f.write(rendered + "\n")
    return rendered


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--live", action="store_true",
                         help="generate with `claude -p` (costs tokens)")
    source.add_argument("--replay", metavar="DIR",
                         help="replay a recordings directory, no model calls")
    parser.add_argument("--ruleset", default="slopwatch")
    parser.add_argument("--out", default=None,
                         help="directory for result.json, report.txt and texts/")
    parser.add_argument("--prompt-set", default="technical",
                         choices=sorted(prompt_set.PROMPT_SETS),
                         help="technical = real content, a fair base rate; "
                              "padding = chosen to produce flags, never a "
                              "base rate")
    parser.add_argument("--prompt", action="append", dest="prompt_ids",
                         help="run only this prompt id (repeatable)")
    parser.add_argument("--enforce", default="lexical",
                         choices=sorted(harness.PRESETS),
                         help="which checks the gated loop enforces: lexical "
                              "(the original 11) or structural (those plus the "
                              "six document-shape checks)")
    parser.add_argument("--max-iterations", type=int, default=4)
    parser.add_argument("--workers", type=int, default=1,
                         help="run this many PROMPTS at once; a prompt's own "
                              "arms always stay sequential")
    args = parser.parse_args(argv)

    try:
        chosen = prompt_set.by_ids(args.prompt_ids, prompt_set=args.prompt_set)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    ruleset = rulesets.get_ruleset(args.ruleset)
    if args.live:
        out_dir = args.out or "evalab-runs/latest"
        generator = ClaudeCliGenerator(
            record_to=os.path.join(out_dir, "recordings"))
    else:
        generator = RecordedGenerator(args.replay)
        out_dir = args.out

    def progress(prompt_id):
        print(f"  {prompt_id} ...", file=sys.stderr, flush=True)

    print(f"running {len(chosen)} {args.prompt_set} prompt(s) against "
          f"{args.ruleset}", file=sys.stderr)
    try:
        result = harness.run(chosen, ruleset, generator,
                              enforced=args.enforce,
                              max_iterations=args.max_iterations,
                              on_progress=progress, workers=args.workers)
        result["prompt_set"] = args.prompt_set
        result["enforce"] = args.enforce
    except GeneratorError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    rendered = _save(out_dir, result) if out_dir else report.render(result)
    print(rendered)
    if out_dir:
        print(f"\nwrote {out_dir}/result.json, report.txt and texts/",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
