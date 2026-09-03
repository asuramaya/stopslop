```python
import fnmatch
import os
from pathlib import Path


def find_files(root, pattern, max_depth=None):
    """Return sorted paths under `root` whose names match `pattern`.

    Hidden entries (names starting with ".") are skipped, as are symlinked
    files. Symlinked directories are not descended into, so a link pointing
    back up the tree cannot send the walk around forever.

    `max_depth` limits how far below `root` the walk goes: 0 searches only
    `root` itself, 1 adds its immediate subdirectories, and None is unlimited.

    The pattern is matched against the file name alone (``*.py``) unless it
    contains a separator, in which case it is matched against the path
    relative to `root` (``src/*/test_*.py``).
    """
    root = Path(root)
    if not root.is_dir():
        raise NotADirectoryError(root)
    if max_depth is not None and max_depth < 0:
        raise ValueError(f"max_depth must be non-negative, got {max_depth}")

    match_full_path = os.sep in pattern or "/" in pattern
    normalized = pattern.replace("/", os.sep)
    matches = []

    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        depth = len(Path(dirpath).relative_to(root).parts)
        if max_depth is not None and depth >= max_depth:
            dirnames[:] = []
        else:
            dirnames[:] = [
                d
                for d in dirnames
                if not d.startswith(".")
                and not os.path.islink(os.path.join(dirpath, d))
            ]

        for name in filenames:
            if name.startswith("."):
                continue
            full = Path(dirpath) / name
            if full.is_symlink():
                continue
            candidate = str(full.relative_to(root)) if match_full_path else name
            if fnmatch.fnmatch(candidate, normalized):
                matches.append(full)

    return sorted(matches)
```
