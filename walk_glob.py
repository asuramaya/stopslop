"""Walk a directory tree and collect files matching a glob pattern."""

import os
from fnmatch import fnmatch
from pathlib import Path
from typing import Iterator


def find_files(
    root: str | Path,
    pattern: str = "*",
    follow_symlinks: bool = False,
) -> Iterator[Path]:
    """Yield every file under `root` whose name matches `pattern`.

    Directories whose name starts with a dot are pruned, so nothing under
    `.git` or `.venv` is ever visited. Symlinks are skipped by default,
    both the links themselves and any directory they point at; that keeps
    a link cycle from turning the walk into an infinite loop, and keeps a
    link out of the tree from pulling in files outside `root`. Pass
    `follow_symlinks=True` if you want them followed anyway.

    `pattern` is matched against the file name alone, not the path, so
    "*.py" works but "src/*.py" never matches. Case sensitivity follows
    the platform, since fnmatch normalizes case the way the OS does.

    The walk is lazy: results arrive directory by directory rather than
    after the whole tree has been read.
    """
    root = Path(root)
    for dirpath, dirnames, filenames in os.walk(root, followlinks=follow_symlinks):
        dirnames[:] = [
            d
            for d in dirnames
            if not d.startswith(".")
            and (follow_symlinks or not os.path.islink(os.path.join(dirpath, d)))
        ]
        dirnames.sort()
        for name in sorted(filenames):
            if not fnmatch(name, pattern):
                continue
            full = os.path.join(dirpath, name)
            if not follow_symlinks and os.path.islink(full):
                continue
            yield Path(full)
