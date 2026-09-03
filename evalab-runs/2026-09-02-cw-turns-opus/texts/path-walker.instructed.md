```python
import fnmatch
import logging
import os
from typing import Iterator

logger = logging.getLogger(__name__)


def find_matching_files(
    root: str, pattern: str, max_depth: int | None = None
) -> Iterator[str]:
    """Yield paths of files under `root` whose name matches `pattern`.

    The pattern is matched against the file's base name using shell-style
    globbing (`*.py`, `test_*.json`). Hidden entries and symlinks are
    skipped, and a directory whose (device, inode) pair has already been
    visited is pruned, so bind mounts and recursive mounts cannot make the
    walk repeat forever.

    `max_depth` limits how far below `root` the walk descends: 0 yields
    only files directly in `root`, 1 also covers its immediate subdirs,
    and None means no limit. Paths are yielded in sorted order, so the
    whole tree is read before the first result.
    """
    if max_depth is not None and max_depth < 0:
        raise ValueError(f"max_depth must be non-negative, got {max_depth}")

    def on_walk_error(err: OSError) -> None:
        logger.warning("cannot list %s: %s", err.filename, err)

    root = os.path.normpath(root)
    root_depth = root.count(os.sep)
    visited: set[tuple[int, int]] = set()
    matches: list[str] = []

    for current_dir, subdirs, filenames in os.walk(
        root, onerror=on_walk_error, followlinks=False
    ):
        try:
            info = os.stat(current_dir)
        except OSError as err:
            logger.warning("cannot stat %s: %s", current_dir, err)
            subdirs.clear()
            continue

        if (info.st_dev, info.st_ino) in visited:
            subdirs.clear()
            continue
        visited.add((info.st_dev, info.st_ino))

        depth = os.path.normpath(current_dir).count(os.sep) - root_depth
        if max_depth is not None and depth >= max_depth:
            subdirs.clear()
        else:
            subdirs[:] = [
                name
                for name in subdirs
                if not name.startswith(".")
                and not os.path.islink(os.path.join(current_dir, name))
            ]

        for name in filenames:
            if name.startswith("."):
                continue
            if not fnmatch.fnmatch(name, pattern):
                continue
            path = os.path.join(current_dir, name)
            if os.path.islink(path):
                continue
            matches.append(path)

    yield from sorted(matches)
```
