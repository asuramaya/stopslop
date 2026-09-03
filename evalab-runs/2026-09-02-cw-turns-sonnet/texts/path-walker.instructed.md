```python
import fnmatch
import logging
import os

logger = logging.getLogger(__name__)


def find_matching_files(root_dir, pattern, max_depth=None):
    """Walk root_dir recursively and return sorted paths of files matching a glob pattern."""
    if not os.path.isdir(root_dir):
        raise NotADirectoryError(f"not a directory: {root_dir}")

    root_dir = os.path.normpath(root_dir)
    matches = []
    for dirpath, dirnames, filenames in os.walk(root_dir, followlinks=False):
        depth = dirpath[len(root_dir):].count(os.sep)
        if max_depth is not None and depth >= max_depth:
            dirnames[:] = []
        dirnames[:] = [
            d for d in dirnames
            if not d.startswith(".") and not os.path.islink(os.path.join(dirpath, d))
        ]
        for filename in filenames:
            full_path = os.path.join(dirpath, filename)
            if filename.startswith(".") or os.path.islink(full_path):
                continue
            if fnmatch.fnmatch(filename, pattern):
                matches.append(full_path)

    matches.sort()
    logger.debug("found %d files matching %r under %s", len(matches), pattern, root_dir)
    return matches


def find_matching_dirs(root_dir, pattern, max_depth=None):
    """Walk root_dir recursively and return sorted paths of directories matching a glob pattern."""
    if not os.path.isdir(root_dir):
        raise NotADirectoryError(f"not a directory: {root_dir}")

    root_dir = os.path.normpath(root_dir)
    matches = []
    for dirpath, dirnames, _ in os.walk(root_dir, followlinks=False):
        depth = dirpath[len(root_dir):].count(os.sep)
        if max_depth is not None and depth >= max_depth:
            dirnames[:] = []
        dirnames[:] = [
            d for d in dirnames
            if not d.startswith(".") and not os.path.islink(os.path.join(dirpath, d))
        ]
        for dirname in dirnames:
            if fnmatch.fnmatch(dirname, pattern):
                matches.append(os.path.join(dirpath, dirname))

    matches.sort()
    return matches
```
