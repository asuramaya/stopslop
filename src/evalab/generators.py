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
import threading
import time


class GeneratorError(RuntimeError):
    """A generation failed. `transient` says whether retrying could help."""

    def __init__(self, message, transient=True):
        super().__init__(message)
        self.transient = transient


# Stderr fragments that mean the command itself is wrong, not that the
# service hiccuped. Retrying these is three wasted model calls before the
# real problem surfaces -- which is exactly what happened when a skill
# file's YAML front matter was passed on argv and read as an unknown
# option, killing every competitor arm at once and retrying each three
# times first.
PERMANENT_SIGNATURES = (
    "unknown option",
    "unknown command",
    "unrecognized option",
    "invalid argument",
    "usage:",
    "no such file or directory",
    "permission denied",
)


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

    def __init__(self, executable="claude", timeout=240, record_to=None,
                  attempts=3, backoff=5):
        self.executable = executable
        self.timeout = timeout
        self.record_to = record_to
        # A 30-prompt run is ~260 subprocesses. At that count a transient
        # non-zero exit is not an anomaly, it is expected, and the first
        # live structural+instructed run died on one at call ~258 of 264
        # -- exit 1 with an EMPTY stderr, nothing to diagnose. Retrying a
        # handful of times is the difference between losing 25 minutes of
        # generations and not. A failure that survives every attempt
        # still raises: this widens the window, it does not paper over a
        # broken executable.
        self.attempts = max(1, attempts)
        self.backoff = backoff
        self._seen = {}
        # A run may drive several prompts at once (harness.run's workers).
        # Two threads bumping the same digest without this would hand both
        # the same occurrence number and one would overwrite the other's
        # recording.
        self._lock = threading.Lock()

    def version(self):
        try:
            out = subprocess.run([self.executable, "--version"],
                                  capture_output=True, text=True, timeout=30)
            return out.stdout.strip() or "unknown"
        except (OSError, subprocess.SubprocessError):
            return "unknown"

    def __call__(self, messages):
        last = None
        for attempt in range(self.attempts):
            try:
                text = self._once(messages)
            except GeneratorError as exc:
                last = exc
                if not getattr(exc, "transient", True):
                    # A wrong command line or a missing executable will
                    # fail identically every time. Surfacing it now costs
                    # one call instead of three, and says what is wrong
                    # instead of burying it under a backoff.
                    raise
                if attempt + 1 < self.attempts:
                    time.sleep(self.backoff * (attempt + 1))
                continue
            if self.record_to:
                self._record(messages, text)
            return text
        raise last

    def _once(self, messages):
        prompt = "\n\n".join(m["content"] for m in messages)
        try:
            # The prompt goes on STDIN, never argv. A skill file opens
            # with YAML front matter, so `claude -p ---\nname: ...` is
            # read as an unknown option and the whole run dies -- which
            # is exactly how the first leaderboard run failed, on every
            # competitor at once. Stdin also sidesteps the argv length
            # limit, and one vendored intervention is 35KB.
            proc = subprocess.run(
                [self.executable, "-p"], input=prompt,
                capture_output=True, text=True, timeout=self.timeout)
        except OSError as exc:
            # The executable is missing or unrunnable. No number of
            # retries makes it appear.
            raise GeneratorError(f"could not run {self.executable!r}: {exc}",
                                  transient=False) from exc
        except subprocess.TimeoutExpired as exc:
            raise GeneratorError(f"{self.executable} timed out after "
                                  f"{self.timeout}s") from exc
        if proc.returncode != 0:
            stderr = proc.stderr.strip()
            lowered = stderr.lower()
            permanent = any(sig in lowered for sig in PERMANENT_SIGNATURES)
            raise GeneratorError(
                f"{self.executable} exited {proc.returncode}: {stderr[:400]}",
                transient=not permanent)
        text = proc.stdout.strip()
        if not text:
            raise GeneratorError(f"{self.executable} returned nothing")
        return text

    def _record(self, messages, text):
        os.makedirs(self.record_to, exist_ok=True)
        key = _key(messages, self._bump(messages))
        with open(os.path.join(self.record_to, key + ".json"), "w") as f:
            json.dump({"messages": messages, "output": text}, f, indent=1)
            f.write("\n")

    def _bump(self, messages):
        digest = _key(messages).rsplit(".", 1)[0]
        with self._lock:
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


class ResumingGenerator:
    """Replays a recording when one exists, generates when it does not.

    A live run is a couple of hundred subprocesses over half an hour.
    Losing all of them because the last one failed is not acceptable, and
    it happened: the first structural+instructed run died at call ~258 of
    264 and the only way to finish was to pay for the other 257 again.

    Resume is safe here for the reason replay is safe. A recording is
    keyed by the exact message list plus how many times that list has been
    asked this run, so a resumed call either matches the question the
    recorded answer belongs to or misses and is generated fresh. It cannot
    hand back an answer to a different question -- the failure mode a
    naive cache would have.

    The inner live generator must NOT record. This one owns the occurrence
    counter, and two counters over one directory would disagree.
    """

    name = "resuming"

    def __init__(self, directory, live):
        if getattr(live, "record_to", None):
            raise ValueError(
                "the inner generator must not record: ResumingGenerator "
                "owns the occurrence counter and two would disagree")
        self.directory = directory
        self.live = live
        self._seen = {}
        self._lock = threading.Lock()
        self.replayed = 0
        self.generated = 0

    def version(self):
        return self.live.version()

    def __call__(self, messages):
        digest = _key(messages).rsplit(".", 1)[0]
        with self._lock:
            occurrence = self._seen.get(digest, 0)
            self._seen[digest] = occurrence + 1
        path = os.path.join(self.directory, f"{digest}.{occurrence}.json")
        if os.path.exists(path):
            with open(path) as f:
                self.replayed += 1
                return json.load(f)["output"]
        text = self.live(messages)
        os.makedirs(self.directory, exist_ok=True)
        with open(path, "w") as f:
            json.dump({"messages": messages, "output": text}, f, indent=1)
            f.write("\n")
        self.generated += 1
        return text
