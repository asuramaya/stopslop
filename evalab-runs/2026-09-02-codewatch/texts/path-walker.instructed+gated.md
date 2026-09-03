```python
import fnmatch
import os
from pathlib import Path


def find_matching_files(root, pattern, follow_symlinks=False):
    """Yield paths under `root` whose file name matches `pattern`.

    Hidden directories (leading dot) are never descended into, and symlinks
    are skipped unless `follow_symlinks` is set. Directories that cannot be
    read are reported through the returned error list rather than raising.
    """
    root = Path(root)
    matches = []
    unreadable = []

    for dirpath, dirnames, filenames in os.walk(
        root, followlinks=follow_symlinks, onerror=unreadable.append
    ):
        dirnames[:] = [
            name
            for name in dirnames
            if not name.startswith(".")
            and (follow_symlinks or not os.path.islink(os.path.join(dirpath, name)))
        ]

        for name in filenames:
            if not fnmatch.fnmatch(name, pattern):
                continue
            full = os.path.join(dirpath, name)
            if not follow_symlinks and os.path.islink(full):
                continue
            matches.append(Path(full))

    return matches, unreadable
```

The pattern matches against the file name alone, so `*.py` works but `src/*.py` will not — pass a name-level glob. Hidden *files* still match; only hidden directories are pruned. `unreadable` collects `OSError` instances for directories `os.walk` could not list (permissions, races), so a partial result is distinguishable from a clean empty one.
