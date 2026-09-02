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
from evalab import harness, interventions, prompts as prompt_set, report
from evalab.generators import (ClaudeCliGenerator, GeneratorError,
                                RecordedGenerator, ResumingGenerator)


def _save(out_dir, result):
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "result.json"), "w") as f:
        json.dump(result, f, indent=1)
        f.write("\n")
    text_dir = os.path.join(out_dir, "texts")
    os.makedirs(text_dir, exist_ok=True)
    for row in result["rows"]:
        saved_arms = ["ungated", "instructed", "gated"]
        saved_arms += result.get("intervention_arms") or []
        saved_arms += result.get("combined_arms") or []
        for arm in saved_arms:
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
    source.add_argument("--resume", metavar="DIR",
                         help="replay what DIR already holds and generate "
                              "only what it does not -- for finishing a live "
                              "run that died partway")
    parser.add_argument("--ruleset", default="slopwatch")
    parser.add_argument("--out", default=None,
                         help="directory for result.json, report.txt and texts/")
    parser.add_argument("--prompt-set", default="technical",
                         help="a built-in set (" +
                              ", ".join(sorted(prompt_set.PROMPT_SETS)) +
                              ") or a PATH to your own: technical = real "
                              "content, a fair base rate; padding = chosen to "
                              "produce flags, never a base rate. Your own is "
                              "the only one that measures YOUR writing -- a "
                              "JSON list of {id, text}, or markdown with '## "
                              "id' headings")
    parser.add_argument("--prompt", action="append", dest="prompt_ids",
                         help="run only this prompt id (repeatable)")
    parser.add_argument("--enforce", default="lexical",
                         choices=sorted(harness.PRESETS),
                         help="which checks the gated loop enforces: lexical "
                              "(the original 11) or structural (those plus the "
                              "six document-shape checks)")
    parser.add_argument("--compare", action="append", dest="compare",
                         metavar="NAME",
                         help="also run a competing intervention as its own "
                              "arm, by name from src/evalab/interventions/ "
                              "(repeatable; 'all' runs every vendored one)")
    parser.add_argument("--combine", action="append", dest="combine",
                         metavar="NAME",
                         help="also run an arm that states NAME's rules up "
                              "front AND runs the gated loop -- does "
                              "instruction stack with enforcement, or compete "
                              "with it? ('all' combines every chosen "
                              "intervention; 'instructed' is this project's "
                              "own block)")
    parser.add_argument("--complement", action="store_true",
                         help="add an arm instructed from the HELD-OUT checks "
                              "-- the ones the gate does not enforce. For that "
                              "arm held-out flags measure instruction-following "
                              "rather than transfer; read total tells")
    parser.add_argument("--max-iterations", type=int, default=4)
    parser.add_argument("--workers", type=int, default=1,
                         help="run this many PROMPTS at once; a prompt's own "
                              "arms always stay sequential")
    args = parser.parse_args(argv)

    try:
        if args.prompt_set in prompt_set.PROMPT_SETS:
            chosen = prompt_set.by_ids(args.prompt_ids,
                                        prompt_set=args.prompt_set)
        else:
            loaded = prompt_set.load_set(args.prompt_set)
            wanted = set(args.prompt_ids or [])
            chosen = [p for p in loaded if not wanted or p["id"] in wanted]
            missing = wanted - {p["id"] for p in loaded}
            if missing:
                raise ValueError(f"unknown prompt id(s): {sorted(missing)}")
            if not chosen:
                raise ValueError(f"{args.prompt_set}: no prompts selected")
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    chosen_interventions = {}
    if args.compare:
        names = (interventions.available() if "all" in args.compare
                  else args.compare)
        for name in names:
            try:
                chosen_interventions[name] = interventions.load(name)
            except (KeyError, FileNotFoundError, OSError) as exc:
                print(f"error: {exc}", file=sys.stderr)
                return 2

    combined = []
    if args.combine:
        combined = (["instructed"] + sorted(chosen_interventions)
                     if "all" in args.combine else list(args.combine))
        if args.complement and "all" in args.combine:
            combined.append("complement")

    ruleset = rulesets.get_ruleset(args.ruleset)
    if args.live:
        out_dir = args.out or "evalab-runs/latest"
        generator = ClaudeCliGenerator(
            record_to=os.path.join(out_dir, "recordings"))
    elif args.resume:
        # The recordings directory is the run's own, so --out defaults to
        # its parent: a resumed run finishes the run it is resuming
        # rather than scattering a second one beside it.
        out_dir = args.out or os.path.dirname(args.resume.rstrip("/"))
        generator = ResumingGenerator(args.resume, ClaudeCliGenerator())
    else:
        generator = RecordedGenerator(args.replay)
        out_dir = args.out

    def progress(prompt_id):
        print(f"  {prompt_id} ...", file=sys.stderr, flush=True)

    print(f"running {len(chosen)} {args.prompt_set} prompt(s) against "
          f"{args.ruleset}", file=sys.stderr)
    for name in sorted(chosen_interventions):
        meta = interventions.provenance(name)
        print(f"  vs {name} ({meta['upstream']}, {meta['license']})",
              file=sys.stderr)
    try:
        result = harness.run(chosen, ruleset, generator,
                              enforced=args.enforce,
                              max_iterations=args.max_iterations,
                              on_progress=progress, workers=args.workers,
                              instructions=chosen_interventions or None,
                              combined=combined,
                              complement=args.complement)
        result["prompt_set"] = args.prompt_set
        result["enforce"] = args.enforce
    except GeneratorError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if isinstance(generator, ResumingGenerator):
        print(f"resumed: {generator.replayed} replayed, "
              f"{generator.generated} newly generated", file=sys.stderr)
    rendered = _save(out_dir, result) if out_dir else report.render(result)
    print(rendered)
    if out_dir:
        print(f"\nwrote {out_dir}/result.json, report.txt and texts/",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
