#!/usr/bin/env python3
"""Where the text under test comes from.

A generator takes a list of messages and returns a string. Two exist. The
CLI one shells out to `claude -p` and costs real tokens. The recorded one
replays a saved run from disk and costs nothing, which is what lets the
tests and CI exercise the harness without a model.

The recorded generator keys on the exact message list PLUS how many times
that list has been asked this run, so a replay that drifts from the run it
was recorded against raises instead of quietly answering the wrong
question, and two independent samples of one prompt stay two samples
rather than collapsing into one. See _key.
"""
import hashlib
import json
import os
import subprocess


class GeneratorError(RuntimeError):
    pass


def _key(messages, occurrence=0):
    """Recording filename: a hash of the messages, plus which time this
    exact message list was asked for.

    The occurrence suffix is not decoration. The control arm sends the
    IDENTICAL message list as the ungated arm, on purpose -- that is what
    makes it a second independent sample. Keying on the messages alone
    handed both arms the same recording, so a replayed run reported a
    noise floor of exactly zero and every gate delta looked significant.
    An instrument that reports no variance because it asked the same
    question twice and cached the answer is worse than no instrument.
    """
    blob = json.dumps(messages, sort_keys=True, ensure_ascii=False)
    digest = hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]
    return f"{digest}.{occurrence}"


class ClaudeCliGenerator:
    """Runs `claude -p`, one process per call.

    Every call is independent: the whole conversation so far is flattened
    into the prompt rather than kept in a session. A revision has to carry
    its own history anyway, and a fresh process keeps one arm from
    inheriting state from the other.
    """

    name = "claude-cli"

    def __init__(self, executable="claude", timeout=240, record_to=None):
        self.executable = executable
        self.timeout = timeout
        self.record_to = record_to
        self._seen = {}

    def version(self):
        try:
            out = subprocess.run([self.executable, "--version"],
                                  capture_output=True, text=True, timeout=30)
            return out.stdout.strip() or "unknown"
        except (OSError, subprocess.SubprocessError):
            return "unknown"

    def __call__(self, messages):
        prompt = "\n\n".join(m["content"] for m in messages)
        try:
            proc = subprocess.run(
                [self.executable, "-p", prompt],
                capture_output=True, text=True, timeout=self.timeout)
        except OSError as exc:
            raise GeneratorError(f"could not run {self.executable!r}: {exc}") from exc
        except subprocess.TimeoutExpired as exc:
            raise GeneratorError(f"{self.executable} timed out after "
                                  f"{self.timeout}s") from exc
        if proc.returncode != 0:
            raise GeneratorError(
                f"{self.executable} exited {proc.returncode}: "
                f"{proc.stderr.strip()[:400]}")
        text = proc.stdout.strip()
        if not text:
            raise GeneratorError(f"{self.executable} returned nothing")
        if self.record_to:
            self._record(messages, text)
        return text

    def _record(self, messages, text):
        os.makedirs(self.record_to, exist_ok=True)
        key = _key(messages, self._bump(messages))
        with open(os.path.join(self.record_to, key + ".json"), "w") as f:
            json.dump({"messages": messages, "output": text}, f, indent=1)
            f.write("\n")

    def _bump(self, messages):
        digest = _key(messages).rsplit(".", 1)[0]
        seen = self._seen.get(digest, 0)
        self._seen[digest] = seen + 1
        return seen


class RecordedGenerator:
    """Replays a directory of recordings written by ClaudeCliGenerator.

    A miss raises. The alternative -- returning something plausible --
    would let a changed prompt silently score against an answer to a
    different question, which is the one failure this harness cannot
    afford.
    """

    name = "recorded"

    def __init__(self, directory):
        self.directory = directory
        self.calls = 0
        self._seen = {}

    def version(self):
        return f"recorded:{os.path.basename(self.directory.rstrip('/'))}"

    def __call__(self, messages):
        digest = _key(messages).rsplit(".", 1)[0]
        occurrence = self._seen.get(digest, 0)
        self._seen[digest] = occurrence + 1
        path = os.path.join(self.directory, f"{digest}.{occurrence}.json")
        if not os.path.exists(path):
            raise GeneratorError(
                f"no recording #{occurrence} for this prompt in "
                f"{self.directory} -- the run being replayed asked this "
                "same question fewer times than this one does. Re-record "
                "with the live generator.")
        with open(path) as f:
            self.calls += 1
            return json.load(f)["output"]


class ScriptedGenerator:
    """Returns queued strings in order. For tests only."""

    name = "scripted"

    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.seen = []

    def version(self):
        return "scripted"

    def __call__(self, messages):
        self.seen.append(messages)
        if not self.outputs:
            raise GeneratorError("scripted generator ran out of outputs")
        return self.outputs.pop(0)
