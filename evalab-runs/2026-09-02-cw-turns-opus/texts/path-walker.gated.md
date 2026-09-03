Nothing to change — `walk_glob.py:10` already does both.

**Sorted return.** `walk_glob.py:62-64` accumulates into a list and returns `sorted(matches)`. The result is a `list[Path]` in path order, not a generator, so you can index it and take its length.

**`max_depth`.** Keyword-only, `walk_glob.py:10`, checked at `:27-28` and enforced at `:36-39` by clearing `dirnames` in place, which prunes before descent rather than filtering results after.

Depth counts directory levels below `root`: `0` is root-only, `1` adds immediate subdirectories, `None` (default) is unlimited. `-1` raises `ValueError`.

That's what the run above shows: `max_depth=0` → `a.py`; `1` adds `src/c.py`; `2` adds `src/pkg/d.py`; unlimited also reaches `src/pkg/deep/e.py`. Sorting held, and `src/link.py` stayed out of every result.

One caveat on the depth semantics, since it's the kind of off-by-one that bites: `max_depth=1` does **not** mean "one level of recursion past root's children" — it means files at relative depth ≤ 1. If you meant the other convention, that's a one-line change at `:38`, but I'd want you to say so before I touch the file.

Which brings me to what I did not do. I didn't edit `walk_glob.py`. It has uncommitted work in it from Ooblek XXIII, who's live in this tree right now, and their diff is precisely what removed `follow_symlinks` and added `max_depth` — the two things this thread has been circling. Writing over it would take out work in flight for no gain, since the features you asked for are the ones already there.

If the version you're running lacks these, you're on the `HEAD` checkout, which yields lazily and has neither argument. Say the word and I'll write the standalone ~40-line file instead of editing the shared one.
