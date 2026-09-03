```python
import fnmatch
import os
from pathlib import Path


def find_matching_files(root, pattern, max_depth=None, skip_hidden=True):
    """Return sorted paths under `root` whose name matches the glob `pattern`.

    Matching is done on each entry's own name, so "*.py" matches any Python
    file at any depth. Directory symlinks are pruned rather than descended
    into, so the walk stays inside `root` and cannot cycle; symlinked files
    are skipped as well.

    Args:
        root: Directory to search. May be a str or Path.
        pattern: A glob such as "*.py" or "test_*.txt".
        max_depth: How many directory levels below `root` to descend. 0 looks
            only at files directly in `root`; None means no limit.
        skip_hidden: Prune dot-directories and skip dotfiles.

    Returns:
        A list of Path objects in sorted order.

    Raises:
        NotADirectoryError: If `root` is not a directory.
        ValueError: If `max_depth` is negative.
    """
    root = Path(root)
    if not root.is_dir():
        raise NotADirectoryError(f"not a directory: {root}")
    if max_depth is not None and max_depth < 0:
        raise ValueError(f"max_depth must be non-negative, got {max_depth}")

    matches = []

    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        depth = len(Path(dirpath).relative_to(root).parts)
        if max_depth is not None and depth >= max_depth:
            dirnames[:] = []
        else:
            dirnames[:] = [
                name
                for name in dirnames
                if not (skip_hidden and name.startswith("."))
                and not os.path.islink(os.path.join(dirpath, name))
            ]

        for name in filenames:
            if skip_hidden and name.startswith("."):
                continue
            full_path = os.path.join(dirpath, name)
            if os.path.islink(full_path):
                continue
            if fnmatch.fnmatch(name, pattern):
                matches.append(Path(full_path))

    return sorted(matches)
```
