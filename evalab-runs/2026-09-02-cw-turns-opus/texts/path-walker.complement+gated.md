```python
import fnmatch
import os
from pathlib import Path


def find_files(root, pattern="*", max_depth=None):
    """Return sorted paths of files under `root` whose name matches `pattern`.

    Hidden entries (name starting with ".") and symlinks are skipped, and each
    physical directory is visited at most once, so the walk terminates even if
    the tree contains a cycle introduced by bind mounts.

    `pattern` is a glob applied to the file name only (e.g. "*.py"), unless it
    contains a separator, in which case it is matched against the path relative
    to `root` (e.g. "src/*/test_*.py").

    `max_depth` limits how deep the walk descends: None is unlimited, 0 lists
    only files directly in `root`, 1 also lists its immediate subdirectories.
    """
    root = Path(root)
    if not root.is_dir():
        raise NotADirectoryError(root)
    if max_depth is not None and max_depth < 0:
        raise ValueError(f"max_depth must be non-negative, got {max_depth}")

    match_on_relpath = os.sep in pattern or "/" in pattern
    normalized = pattern.replace("/", os.sep)
    matches = []
    visited = set()

    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        base = Path(dirpath)
        info = os.stat(dirpath)
        if (info.st_dev, info.st_ino) in visited:
            dirnames[:] = []
            continue
        visited.add((info.st_dev, info.st_ino))

        relative = base.relative_to(root)
        depth = 0 if relative == Path(".") else len(relative.parts)

        # Pruning in place stops os.walk from descending; symlinked directories
        # are dropped here rather than by followlinks, which would still list them.
        if max_depth is not None and depth >= max_depth:
            dirnames[:] = []
        else:
            dirnames[:] = [
                d
                for d in dirnames
                if not d.startswith(".") and not (base / d).is_symlink()
            ]

        for name in filenames:
            if name.startswith("."):
                continue
            full = base / name
            if full.is_symlink():
                continue
            candidate = str(full.relative_to(root)) if match_on_relpath else name
            if fnmatch.fnmatch(candidate, normalized):
                matches.append(full)

    return sorted(matches)
```
