#!/usr/bin/env python3
"""Measurements over a piece of generated text.

Two families, and the split is the whole point of the experiment.

FLAG COUNTS come from a ruleset's own checks. They are what the gate
optimizes, so a gated arm scoring better on an ENFORCED check proves
nothing at all: the loop ran until that check went quiet. Only a HELD-OUT
check -- one the gated arm never saw and never had to satisfy -- carries
information about whether anything transferred.

SHAPE METRICS come from the text alone and match no check in any ruleset.
They exist because the interesting failure mode is not "the model keeps a
banned construction", it is "the model flattens everything into one
register to be safe". Sentence-length standard deviation is the direct
measure of that: prose that varies between a four-word sentence and a
thirty-word one has a high one, and clipped three-beat declaratives all
the way down have a low one. No check in this project rewards or punishes
that number, so nothing can be tuned to it.

Sentences come from core.blocks.tokenize_sentences, the same tokenizer
the rulesets themselves use. A second sentence splitter here would drift
from the one doing the gating and quietly make the two arms
incomparable.
"""
import os
import re
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.blocks import split_into_blocks, tokenize_sentences

_WORD_RE = re.compile(r"[A-Za-z][A-Za-z'-]*")


def prose_sentences(text):
    """Sentences of real prose, with fenced code and inline code removed.

    Mirrors what slopwatch's own lint_and_gate does before it counts
    anything, so a shape metric and a flag count describe the same text.
    """
    sentences = []
    for block_type, content in split_into_blocks(text):
        if block_type in ("fence", "blank"):
            continue
        content = re.sub(r"`[^`\n]+`", " ", content)
        sentences.extend(tokenize_sentences(content))
    return [s for s in sentences if _WORD_RE.search(s)]


def words(text):
    return _WORD_RE.findall(text.lower())


def word_count(text):
    return len(words(text))


def type_token_ratio(text):
    """Distinct words over total words: a coarse read on vocabulary range.

    Falls with repetition, which is one shape a flattened register takes.
    It is length-sensitive (a longer text repeats more), so compare it
    only between texts of broadly similar length, and read it next to
    word_count rather than on its own.
    """
    tokens = words(text)
    if not tokens:
        return 0.0
    return len(set(tokens)) / len(tokens)


def sentence_length_stats(text):
    """Mean and standard deviation of sentence length, in words.

    The standard deviation is the monotone detector. A low one says every
    sentence is the same size, which is what a controlled register and a
    bored model both produce.
    """
    lengths = [len(words(s)) for s in prose_sentences(text)]
    lengths = [n for n in lengths if n]
    if not lengths:
        return {"sentences": 0, "mean": 0.0, "stdev": 0.0}
    return {
        "sentences": len(lengths),
        "mean": statistics.fmean(lengths),
        "stdev": statistics.stdev(lengths) if len(lengths) > 1 else 0.0,
    }


def flags_per_1k(flag_kinds, text, only=None):
    """Flags per 1000 words, counting only the check ids in `only`.

    Normalized by length because the gated arm is free to produce a
    shorter answer, and a raw count would then reward it for saying
    less.
    """
    total = word_count(text)
    if not total:
        return 0.0
    counted = [k for k in flag_kinds if only is None or k in only]
    return len(counted) * 1000.0 / total


def shape(text):
    """Every metric that needs no ruleset, in one dict."""
    stats = sentence_length_stats(text)
    return {
        "words": word_count(text),
        "sentences": stats["sentences"],
        "mean_sentence_words": round(stats["mean"], 2),
        "sentence_length_stdev": round(stats["stdev"], 2),
        "type_token_ratio": round(type_token_ratio(text), 4),
    }
