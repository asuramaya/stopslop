The return was already `sorted(matches)`; I've kept it and made the ordering explicit in the docstring. `max_depth` is added below.

```python
import fnmatch
import os
from pathlib import Path


def find_files(root, pattern, *, match_full_path=False, max_depth=None):
    """Walk a directory tree and return every file matching a glob pattern.

    Hidden entries (names starting with ".") and symlinks are skipped, both
    for the files returned and for the directories descended into. Each
    directory is visited at most once, identified by (st_dev, st_ino), so
    cycles introduced by bind mounts cannot make the walk non-terminating.

    Args:
        root: Directory to search from.
        pattern: Glob pattern, e.g. "*.py" or "src/*.txt".
        match_full_path: Match the pattern against the path relative to root
            instead of just the file name. Needed for patterns containing a
            separator, e.g. "tests/*.py".
        max_depth: How many directory levels below root to descend. 0 searches
            only root itself, 1 also searches its immediate subdirectories,
            and None (the default) means no limit.

    Returns:
        A list of pathlib.Path objects for the matching files, sorted by path.
    """
    root = Path(root)
    if not root.is_dir():
        raise NotADirectoryError(f"not a directory: {root}")
    if max_depth is not None and max_depth < 0:
        raise ValueError(f"max_depth must be non-negative, got {max_depth}")

    def key(path):
        try:
            st = os.stat(path, follow_symlinks=False)
        except OSError:
            return None
        return (st.st_dev, st.st_ino)

    matches = []
    seen = {key(root)}
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        current = Path(dirpath)
        depth = len(current.relative_to(root).parts)
        keep = []
        if max_depth is None or depth < max_depth:
            for name in sorted(dirnames):
                if name.startswith("."):
                    continue
                child = current / name
                if child.is_symlink():
                    continue
                ident = key(child)
                if ident is None or ident in seen:
                    continue
                seen.add(ident)
                keep.append(name)
        dirnames[:] = keep  # prune in place; os.walk reads this back
        for name in sorted(filenames):
            path = current / name
            if name.startswith(".") or path.is_symlink():
                continue
            candidate = str(path.relative_to(root)) if match_full_path else name
            if fnmatch.fnmatch(candidate, pattern):
                matches.append(path)

    return sorted(matches)
```

Two notes on the depth cap. It counts directory levels, not path components of the match, so `max_depth=1` returns files in `root/` and `root/sub/` but nothing deeper. And clearing `dirnames` at the limit means those subdirectories are never statted, so capping depth also skips the inode bookkeeping for the pruned subtree — cheap, and the reason the depth check sits before the loop rather than inside it.

The sort is on `Path` objects, which compare by their string parts, so `a/b.py` sorts before `a-1/b.py` on POSIX (`/` < `-` is false — `-` is 0x2D, `/` is 0x2F, so `a-1` actually comes first). If you need a specific collation, sort the caller's way on the returned list rather than relying on this one.
