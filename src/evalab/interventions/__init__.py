#!/usr/bin/env python3
"""Competing anti-slop interventions, as prompt prefixes.

This category is almost entirely skill files: instructions loaded into a
model's context, no enforcement of any kind. stop-slop has 16.7k stars,
no-ai-slop 6.6k, and neither publishes a single number about whether it
works. That is not a criticism of their authors -- nobody in this space
measures, because until now nobody had a rig to measure with.

A skill file IS a prompt prefix, so it drops straight into this harness
as an arm. Same 30 prompts, same paired statistics, same replayable
recordings as stopslop's own gate. The point is a leaderboard the
category has never had, and it is a real experiment: a 16.7k-star file
that has been iterated on by thousands of readers may well beat the
block stopslop generates from its own checks. If it does, the wording is
MIT and the right response is to adopt it and re-run.

Each vendored file sits beside its upstream LICENSE. Every one here is
MIT; jalaalrd/anti-ai-slop-writing (432 stars) is deliberately absent
because it ships no license at all, which reserves all rights.

The full skill is used, references included, not just the front matter a
progressive loader would read first. Same rule the harness applies to
its own instruction: compare against the STRONGEST form of the
alternative, never a convenient weakening of it.
"""
import os

_DIR = os.path.dirname(os.path.abspath(__file__))

# name -> (filename, upstream, license, what it is)
CATALOGUE = {
    "stop-slop": ("stop-slop.md", "github.com/hardikpandya/stop-slop", "MIT",
                   "16.7k stars. Skill file plus phrase, structure and "
                   "example references."),
    "no-ai-slop": ("no-ai-slop.md", "github.com/petergyang/no-ai-slop", "MIT",
                    "6.6k stars. Skill file, 20+ named patterns."),
    "anti-slop-writing": ("anti-slop-writing.md",
                           "github.com/adenaufal/anti-slop-writing", "MIT",
                           "121 stars. Universal system prompt, banlist plus "
                           "structural patterns."),
}

TASK_SUFFIX = "\n\nNow write the following. Return only the requested text.\n\n"


def available():
    """Names whose vendored file is actually on disk."""
    return sorted(name for name, (fn, *_) in CATALOGUE.items()
                   if os.path.exists(os.path.join(_DIR, fn)))


def load(name):
    """One intervention's prompt prefix, ready to sit ahead of a prompt.

    The task suffix is appended so every intervention ends the same way
    and the model is told to return only the text. Without it a skill
    file that ends mid-instruction leaves the arm answering a different
    question from every other one.
    """
    if name not in CATALOGUE:
        raise KeyError(f"no intervention named {name!r} -- "
                        f"have {sorted(CATALOGUE)}")
    path = os.path.join(_DIR, CATALOGUE[name][0])
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"{name} is catalogued but not vendored at {path}")
    with open(path) as f:
        return f.read().rstrip() + TASK_SUFFIX


def provenance(name):
    fn, upstream, licence, note = CATALOGUE[name]
    return {"name": name, "file": fn, "upstream": upstream,
            "license": licence, "note": note}
