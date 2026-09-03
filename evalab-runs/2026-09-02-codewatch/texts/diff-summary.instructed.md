```python
from collections import Counter
from typing import NamedTuple


class LineDiff(NamedTuple):
    added: list[str]
    removed: list[str]
    unchanged: list[str]


def diff_lines(before: list[str], after: list[str]) -> LineDiff:
    """Compare two line sequences by content, respecting duplicate counts.

    A line present three times in `before` and once in `after` counts as
    one unchanged occurrence and two removals. Order follows first
    appearance in the list the line came from.
    """
    before_counts = Counter(before)
    after_counts = Counter(after)

    unchanged_budget = before_counts & after_counts
    removed_budget = before_counts - after_counts
    added_budget = after_counts - before_counts

    unchanged: list[str] = []
    removed: list[str] = []
    for line in before:
        if unchanged_budget[line]:
            unchanged_budget[line] -= 1
            unchanged.append(line)
        elif removed_budget[line]:
            removed_budget[line] -= 1
            removed.append(line)

    added: list[str] = []
    for line in after:
        if added_budget[line]:
            added_budget[line] -= 1
            added.append(line)

    return LineDiff(added=added, removed=removed, unchanged=unchanged)


def format_diff(diff: LineDiff) -> str:
    """Render a diff as `+`/`-`/` ` prefixed lines, additions last."""
    rows = [f"-{line}" for line in diff.removed]
    rows += [f" {line}" for line in diff.unchanged]
    rows += [f"+{line}" for line in diff.added]
    return "\n".join(rows)
```
