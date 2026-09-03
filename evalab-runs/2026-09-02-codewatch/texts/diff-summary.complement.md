```python
def diff_lines(before, after):
    """Compare two lists of strings and report what changed.

    Returns a dict with three keys: 'added', 'removed', and 'unchanged'.
    Each maps to a list of (line_number, text) pairs. Line numbers are
    1-based and refer to the list the line was found in -- 'after' for
    added and unchanged lines, 'before' for removed ones.

    Duplicate lines are matched by count, so a line appearing twice in
    'before' and once in 'after' counts as one unchanged and one removed.
    """
    from collections import Counter

    before_counts = Counter(before)
    after_counts = Counter(after)

    added = []
    unchanged = []
    seen = Counter()
    for index, text in enumerate(after, start=1):
        seen[text] += 1
        if seen[text] <= before_counts[text]:
            unchanged.append((index, text))
        else:
            added.append((index, text))

    removed = []
    seen.clear()
    for index, text in enumerate(before, start=1):
        seen[text] += 1
        if seen[text] > after_counts[text]:
            removed.append((index, text))

    return {"added": added, "removed": removed, "unchanged": unchanged}


def format_summary(result):
    """Render the diff_lines result the way a terminal diff would."""
    lines = []
    for number, text in result["removed"]:
        lines.append(f"-{number:>4} {text}")
    for number, text in result["unchanged"]:
        lines.append(f" {number:>4} {text}")
    for number, text in result["added"]:
        lines.append(f"+{number:>4} {text}")
    return "\n".join(lines)
```
