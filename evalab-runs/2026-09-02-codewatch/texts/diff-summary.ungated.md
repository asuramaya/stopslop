`line_diff.py:29` — `diff_lines(old, new) -> DiffSummary`, backed by `difflib.SequenceMatcher`:

```python
@dataclass
class DiffSummary:
    added: list[str]
    removed: list[str]
    unchanged: list[str]

    @property
    def changed(self) -> bool: ...
    def counts(self) -> dict[str, int]: ...
```

Two choices worth naming, since "added/removed/unchanged" is ambiguous on both:

- **Position matters.** A line moved elsewhere in the file shows up as one removal plus one addition, matching what a text diff shows. If you want set semantics instead (membership only, ignoring order), that is a different and much shorter function — say the word and I'll swap it.
- **Duplicates stay separate.** Three identical lines are three entries, not one.

Smoke-tested on a small edit (2 added, 1 removed, 3 unchanged) and on two empty lists.
