```python
import os
from fnmatch import fnmatch


def find_files(root, pattern="*", include_hidden_files=False):
    """Yield paths of files under `root` that match a glob pattern.

    Hidden directories (names starting with ".") are pruned, and symlinks are
    never followed or returned -- neither symlinked directories nor symlinked
    files. `root` itself may be hidden or a symlink; only its contents are
    filtered.

    If `pattern` contains a path separator it is matched against the path
    relative to `root` ("src/*.py"); otherwise against the file name alone
    ("*.py"). Set `include_hidden_files` to also match dotfiles.
    """
    root = os.path.abspath(root)
    match_on_path = os.sep in pattern or "/" in pattern

    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        # Prune in place so os.walk never descends into these.
        dirnames[:] = [
            d for d in sorted(dirnames)
            if not d.startswith(".")
            and not os.path.islink(os.path.join(dirpath, d))
        ]

        for name in sorted(filenames):
            if name.startswith(".") and not include_hidden_files:
                continue

            full = os.path.join(dirpath, name)
            if os.path.islink(full):
                continue

            candidate = os.path.relpath(full, root) if match_on_path else name
            if fnmatch(candidate, pattern):
                yield full
```

Two details worth knowing:

- `followlinks=False` stops `os.walk` from descending through symlinked directories, but it still *lists* them in `dirnames`, so the prune drops them explicitly. Without that they would show up as directories you'd stat.
- `fnmatch` treats `*` as matching `/` too, so `src/*.py` also matches `src/a/b.py`. If you need true glob semantics where `*` stops at a separator, swap the match for `pathlib.PurePath(candidate).full_match(pattern)` (3.13+) or `.match()` on 3.12 and earlier.

I exercised it on a scratch tree with a hidden dir, a symlinked file, and a symlinked dir: all three were skipped, and `*.py`, `b/*/*.py`, and `*` each returned what you'd expect.
