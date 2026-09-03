```python
import fnmatch
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


def find_matching_files(root, pattern, max_depth=None):
    """Walk `root` and return paths of every file whose name matches `pattern`.

    The pattern is matched against each file's name only (e.g. "*.py"), unless
    it contains a path separator, in which case it is matched against the path
    relative to `root` (e.g. "src/*/test_*.py").

    Hidden entries (names beginning with a dot) are skipped, as are symlinks:
    dot directories such as .git and .venv are rarely interesting to a search,
    and symlinks are excluded both to avoid cycles and to keep each file
    reported once, under its real location. Directories reached more than once
    through hard-linked or bind-mounted paths are visited only the first time,
    identified by their (st_dev, st_ino) pair.

    Args:
        root: Directory to walk.
        pattern: Glob pattern, in the style of fnmatch.
        max_depth: How many directory levels below `root` to descend. 0 looks
            at files directly in `root` only; None (the default) is unlimited.

    Returns:
        A list of Path objects, sorted by path.
    """
    root = Path(root)
    if not root.is_dir():
        raise NotADirectoryError(root)
    if max_depth is not None and max_depth < 0:
        raise ValueError(f"max_depth must be non-negative, got {max_depth}")

    match_full_path = os.sep in pattern or "/" in pattern
    normalized = pattern.replace("/", os.sep)
    matches = []
    visited = set()

    def on_walk_error(error):
        logger.warning("skipping %s: %s", error.filename, error)

    def is_unvisited(path):
        try:
            info = os.stat(path, follow_symlinks=False)
        except OSError as error:
            on_walk_error(error)
            return False
        key = (info.st_dev, info.st_ino)
        if key in visited:
            logger.debug("already visited %s, not descending again", path)
            return False
        visited.add(key)
        return True

    is_unvisited(root)

    for dirpath, dirnames, filenames in os.walk(root, onerror=on_walk_error):
        depth = len(Path(dirpath).relative_to(root).parts)
        if max_depth is not None and depth >= max_depth:
            dirnames[:] = []
        else:
            dirnames[:] = [
                name
                for name in dirnames
                if not name.startswith(".")
                and not os.path.islink(os.path.join(dirpath, name))
                and is_unvisited(os.path.join(dirpath, name))
            ]

        for filename in filenames:
            candidate = Path(dirpath) / filename
            if filename.startswith(".") or candidate.is_symlink():
                continue
            subject = str(candidate.relative_to(root)) if match_full_path else filename
            if fnmatch.fnmatch(subject, normalized):
                matches.append(candidate)

    return sorted(matches)
```
