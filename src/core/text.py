"""Tiny text-formatting helpers shared by every entry point that reports a
count back to a person or an agent -- the hook's own deny message, the
CLI, status reports, the dashboard. One function, so "1 flag(s)" cannot
creep back in caller by caller: this project polices exactly that tell
in everyone else's prose, so its own messages do not get to keep it.
"""


def n(count, noun, plural=None):
    """"1 word" / "12 words" -- real pluralization, not a "(s)" suffix.
    `plural` is only for the irregular few (fix -> fixes); every regular
    noun here just takes the bare -s default."""
    if count == 1:
        return f"1 {noun}"
    return f"{count} {plural or noun + 's'}"
