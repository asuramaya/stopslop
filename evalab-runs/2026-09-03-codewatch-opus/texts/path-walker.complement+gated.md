```python
import fnmatch
import os


def find_matching_files(root, pattern, skip_dirs=None, max_depth=None):
    """Walk `root` and return the sorted path of every file matching `pattern`.

    The pattern is matched against the file name alone when it contains no
    separator, and against the path relative to `root` otherwise, so both
    "*.py" and "src/*/test_*.py" behave the way a shell user expects.

    `max_depth` counts directory levels below `root`: 0 searches only `root`
    itself, 1 also searches its immediate subdirectories, and None is
    unlimited. Symlinks are never followed or returned, so a link pointing at
    an ancestor directory cannot send the walk around in circles.
    """
    if skip_dirs is None:
        skip_dirs = {"__pycache__", "node_modules"}
    if max_depth is not None and max_depth < 0:
        raise ValueError("max_depth must be non-negative")

    root = os.path.abspath(root)
    if not os.path.isdir(root):
        raise NotADirectoryError(root)

    match_full_path = os.sep in pattern or "/" in pattern
    normalized = pattern.replace("/", os.sep)
    matches = []

    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        depth = 0 if dirpath == root else dirpath.count(os.sep) - root.count(os.sep)

        if max_depth is not None and depth >= max_depth:
            dirnames[:] = []
        else:
            kept = []
            for name in dirnames:
                if name.startswith(".") or name in skip_dirs:
                    continue
                try:
                    if os.path.islink(os.path.join(dirpath, name)):
                        continue
                except OSError:
                    continue
                kept.append(name)
            dirnames[:] = kept

        for name in filenames:
            if name.startswith("."):
                continue
            full = os.path.join(dirpath, name)
            try:
                if not os.path.isfile(full) or os.path.islink(full):
                    continue
            except OSError:
                continue
            candidate = os.path.relpath(full, root) if match_full_path else name
            if fnmatch.fnmatch(candidate, normalized):
                matches.append(full)

    matches.sort()
    return matches
```
