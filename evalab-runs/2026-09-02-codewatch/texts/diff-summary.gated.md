`line_diff.py` in the working dir already holds exactly this function (untracked, 43 lines). I ran it rather than rewriting it:

```python
diff_lines(['a','b','c','d'], ['a','x','c','d','e'])
# added ['x','e'], removed ['b'], unchanged ['a','c','d'], changed=True
```

How it works:

- `DiffSummary` dataclass with `added` / `removed` / `unchanged` lists, a `changed` property, and `counts()` for the tallies.
- `diff_lines(old, new)` walks `SequenceMatcher(autojunk=False).get_opcodes()`: `equal` blocks go to `unchanged`, everything else splits into `removed` (from old) and `added` (from new).

Two behaviors worth knowing, both documented in the docstring: position matters, so a moved line reads as one removal plus one addition; and duplicate lines stay separate instead of collapsing into a set. `autojunk=False` matters on inputs over 200 lines — without it, SequenceMatcher starts treating frequent lines as junk and silently skews the result.

Want it moved somewhere specific in `src/`, or tests added?
