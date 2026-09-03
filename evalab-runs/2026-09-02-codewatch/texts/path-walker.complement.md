```python
import os
from fnmatch import fnmatch
from pathlib import Path


def find_files(root, pattern="*"):
    """Return the files under root that match a glob pattern.

    Directories whose name starts with a dot are pruned, so nothing inside
    .git or .venv is visited. Symlinks are never followed and symlinked
    files are never returned, so a link pointing back up the tree cannot
    produce a cycle or a duplicate.

    A pattern containing a slash is matched against the path relative to
    root ("src/*.py"); any other pattern is matched against the file name
    alone ("*.py"). Results come back sorted.
    """
    root = Path(root)
    if not root.is_dir():
        raise NotADirectoryError(root)

    match_relative = "/" in pattern
    found = []

    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = [name for name in dirnames if not name.startswith(".")]

        for name in filenames:
            path = Path(dirpath, name)
            if path.is_symlink():
                continue
            subject = path.relative_to(root).as_posix() if match_relative else name
            if fnmatch(subject, pattern):
                found.append(path)

    found.sort()
    return found
```
