```python
from dataclasses import dataclass, field
from difflib import SequenceMatcher


@dataclass
class LineDiff:
    """Line-level comparison of two text revisions."""

    added: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    unchanged: list[str] = field(default_factory=list)

    @property
    def is_identical(self) -> bool:
        return not self.added and not self.removed

    def format_report(self) -> str:
        return (
            f"+{len(self.added)} -{len(self.removed)} "
            f"={len(self.unchanged)}"
        )


def diff_lines(before: list[str], after: list[str]) -> LineDiff:
    """Compare two revisions of a file, line by line.

    Order matters: a line moved from the top of the file to the bottom
    counts as one removal plus one addition, not as unchanged. Duplicate
    lines are tracked by position, so three copies of "" in `before` and
    one in `after` yield two removals.
    """
    diff = LineDiff()
    matcher = SequenceMatcher(a=before, b=after, autojunk=False)

    for tag, before_start, before_end, after_start, after_end in matcher.get_opcodes():
        before_slice = before[before_start:before_end]
        after_slice = after[after_start:after_end]

        if tag == "equal":
            diff.unchanged.extend(before_slice)
        elif tag == "insert":
            diff.added.extend(after_slice)
        elif tag == "delete":
            diff.removed.extend(before_slice)
        else:  # replace
            diff.removed.extend(before_slice)
            diff.added.extend(after_slice)

    return diff
```
