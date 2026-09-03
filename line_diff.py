"""Line-level diff summary between two lists of strings."""

from dataclasses import dataclass, field
from difflib import SequenceMatcher


@dataclass
class DiffSummary:
    """Lines that appear only in new, only in old, and in both."""

    added: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    unchanged: list[str] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return bool(self.added or self.removed)

    def counts(self) -> dict[str, int]:
        return {
            "added": len(self.added),
            "removed": len(self.removed),
            "unchanged": len(self.unchanged),
        }


def diff_lines(old: list[str], new: list[str]) -> DiffSummary:
    """Compare two line lists and report what was added, removed, and kept.

    Position matters: a line moved from the top of the file to the bottom
    counts as one removal and one addition, the same way a text diff sees it.
    Duplicate lines are kept separate rather than collapsed into a set.
    """
    summary = DiffSummary()
    matcher = SequenceMatcher(a=old, b=new, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            summary.unchanged.extend(old[i1:i2])
        else:
            summary.removed.extend(old[i1:i2])
            summary.added.extend(new[j1:j2])
    return summary
