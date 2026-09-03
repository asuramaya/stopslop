```python
import fnmatch
import os


def find_files(root, pattern, follow_symlinks=False):
    """Yield paths under root whose basename matches a glob pattern.

    Hidden directories (leading dot) are never descended into, and symlinked
    files are skipped unless follow_symlinks is set. Directories that cannot
    be read are reported to the caller through on_error, if given.
    """
    matches = []

    for dirpath, dirnames, filenames in os.walk(root, followlinks=follow_symlinks):
        dirnames[:] = [
            d for d in dirnames
            if not d.startswith(".")
            and (follow_symlinks or not os.path.islink(os.path.join(dirpath, d)))
        ]

        for name in filenames:
            if not fnmatch.fnmatch(name, pattern):
                continue
            full = os.path.join(dirpath, name)
            if not follow_symlinks and os.path.islink(full):
                continue
            matches.append(full)

    return matches


def find_files_iter(root, pattern, follow_symlinks=False):
    """Same walk as find_files, but streams results instead of building a list."""
    for dirpath, dirnames, filenames in os.walk(root, followlinks=follow_symlinks):
        dirnames[:] = [
            d for d in dirnames
            if not d.startswith(".")
            and (follow_symlinks or not os.path.islink(os.path.join(dirpath, d)))
        ]

        for name in filenames:
            if not fnmatch.fnmatch(name, pattern):
                continue
            full = os.path.join(dirpath, name)
            if follow_symlinks or not os.path.islink(full):
                yield full
```

One note on the docstring: it mentions an `on_error` parameter that the signature does not have. Drop that sentence, or pass `onerror=on_error` through to `os.walk` — right now a directory that cannot be read is silently skipped by `os.walk`'s default.
