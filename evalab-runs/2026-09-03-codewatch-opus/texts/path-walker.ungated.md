```python
import fnmatch
import os
from pathlib import Path


def find_files(root, pattern, *, max_depth=None, match_full_path=False, skip_hidden=True):
    """Walk a directory tree and return every file matching a glob pattern.

    Symlinks are never followed: symlinked directories are not descended into,
    and symlinked files are not returned. Because no symlink is ever traversed,
    the walk visits each real directory at most once and cannot cycle. Hidden
    entries (names starting with ".") are skipped by default.

    Args:
        root: Directory to search from. Must not itself be a symlink.
        pattern: Glob pattern, e.g. "*.py" or "src/**/*.txt". By default it is
            matched against each file's basename; set match_full_path to match
            against the path relative to root instead (so "**" and "/" work).
        max_depth: How many directory levels below root to descend. 0 searches
            only root itself, 1 also searches its immediate subdirectories, and
            None (the default) means no limit. Must be non-negative.
        match_full_path: Match the relative path rather than the basename.
        skip_hidden: Skip dot-directories and dot-files.

    Returns:
        A list of pathlib.Path objects, one per matching file, sorted by path.
    """
    root = Path(root)
    if root.is_symlink():
        raise ValueError(f"root is a symlink, refusing to traverse: {root}")
    if not root.is_dir():
        raise NotADirectoryError(root)
    if max_depth is not None and max_depth < 0:
        raise ValueError(f"max_depth must be non-negative, got {max_depth}")

    matches = []

    # followlinks=False keeps os.walk from descending into symlinked dirs.
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        # Depth of the directory being visited: 0 for root itself.
        depth = len(Path(dirpath).relative_to(root).parts)

        # Prune in place: os.walk reads this list back after yielding, so
        # filtering a copy would have no effect. Symlinked dirs are dropped
        # here too, which keeps them out of dirpath on the next iteration.
        if max_depth is not None and depth >= max_depth:
            dirnames[:] = []
        else:
            dirnames[:] = [
                d for d in dirnames
                if not (skip_hidden and d.startswith("."))
                and not os.path.islink(os.path.join(dirpath, d))
            ]

        for name in filenames:
            if skip_hidden and name.startswith("."):
                continue
            full = Path(dirpath) / name
            # os.walk still lists symlinked *files* regardless of followlinks.
            if full.is_symlink():
                continue
            if match_full_path:
                rel = full.relative_to(root).as_posix()
                if full.match(pattern) or fnmatch.fnmatch(rel, pattern):
                    matches.append(full)
            elif fnmatch.fnmatch(name, pattern):
                matches.append(full)

    return sorted(matches)
```

The results were already sorted — `return sorted(matches)` has been there since the first version — so that part is unchanged, just documented explicitly in the docstring now.

The depth limit counts levels *below* root, so `max_depth=0` matches only files sitting directly in root and `max_depth=1` adds its immediate subdirectories. It's enforced by clearing `dirnames` rather than by filtering results after the fact, so a shallow search doesn't pay to stat a deep tree. Note that the limit and `skip_hidden` interact in the obvious way: at the cutoff depth every subdirectory is dropped regardless, which is why that branch clears the list outright instead of running the hidden/symlink filter.
