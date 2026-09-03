```python
import os
from fnmatch import fnmatch
from pathlib import Path


def find_files(root, pattern):
    """Return every file under root whose path matches a glob pattern.

    Hidden directories (a leading dot) are not descended into. Symlinks are
    skipped on both sides: a symlinked directory is never followed, and a
    symlinked file is never returned. That keeps a link pointing back up the
    tree from turning the walk into an infinite loop.

    The pattern is matched against the path relative to root, so "*.py"
    catches a file at any depth and "src/*.py" only catches one directly
    under src. Results come back sorted, so two runs over an unchanged tree
    agree.
    """
    root = Path(root).resolve()
    matches = []

    for directory, subdirs, filenames in os.walk(root, followlinks=False):
        directory = Path(directory)

        # Assigning into the slice is what prunes the walk; rebinding the
        # name would leave os.walk with the original list.
        subdirs[:] = [
            name
            for name in subdirs
            if not name.startswith(".") and not (directory / name).is_symlink()
        ]

        for filename in filenames:
            path = directory / filename
            if path.is_symlink():
                continue
            relative = path.relative_to(root)
            if fnmatch(str(relative), pattern) or fnmatch(filename, pattern):
                matches.append(path)

    matches.sort()
    return matches
```
