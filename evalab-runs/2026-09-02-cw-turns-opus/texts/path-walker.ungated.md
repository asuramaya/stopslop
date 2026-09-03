`max_depth` added at `walk_glob.py:10`; the return was already sorted, so only the docstring changed there.

- Depth counts directory levels below `root`. `max_depth=0` visits only files sitting directly in `root`, `1` adds its immediate subdirectories, `None` (default) means no limit.
- Pruning happens by emptying `dirnames[:]` at the limit, so `os.walk` never descends past it rather than walking the whole tree and filtering after.
- A negative `max_depth` raises `ValueError` instead of silently returning nothing.

On this repo: `*.py` gives 19 files at depth 0, 38 at 1, 95 at 2, and 112 unlimited. `evalab-prompts/*.md` still returns the three expected files unlimited, and an empty list at `max_depth=0` — the depth cap applies to where the file lives, not to the shape of the pattern.
