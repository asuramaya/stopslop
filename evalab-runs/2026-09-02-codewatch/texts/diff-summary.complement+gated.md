```python
def summarize_line_changes(old_lines, new_lines, ignore_trailing_ws=True):
    """Compare two sequences of lines and report what changed between them.

    Returns a dict with 'added', 'removed', and 'unchanged' line lists plus
    a 'counts' mapping. Duplicate lines are respected: if a line appears
    three times in old_lines and once in new_lines, two copies land in
    'removed' and one in 'unchanged'.
    """
    if old_lines is None:
        old_lines = []
    if new_lines is None:
        new_lines = []

    def normalize(line):
        return line.rstrip() if ignore_trailing_ws else line

    remaining = {}
    for line in new_lines:
        key = normalize(line)
        remaining[key] = remaining.get(key, 0) + 1

    removed = []
    unchanged = []
    for line in old_lines:
        key = normalize(line)
        if remaining.get(key, 0) > 0:
            remaining[key] -= 1
            unchanged.append(line)
        else:
            removed.append(line)

    # Walk new_lines in order so 'added' keeps the caller's line ordering;
    # the leftover counts in `remaining` are unordered.
    surplus = dict(remaining)
    added = []
    for line in new_lines:
        key = normalize(line)
        if surplus.get(key, 0) > 0:
            surplus[key] -= 1
            added.append(line)

    return {
        "added": added,
        "removed": removed,
        "unchanged": unchanged,
        "counts": {
            "added": len(added),
            "removed": len(removed),
            "unchanged": len(unchanged),
        },
    }
```
