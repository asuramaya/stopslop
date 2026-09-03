```python
import fnmatch
import os
from pathlib import Path


def find_files(root, pattern="*"):
    """Walk `root` and return every file matching `pattern`.

    Hidden directories (names starting with '.') are pruned, and symlinks are
    skipped for both directories and files, so the walk never leaves the tree
    or revisits it through a loop.

    Patterns containing '/' are matched against the path relative to `root`
    ("src/*.py"); patterns without one are matched against the file name alone
    ("*.py"). Results are returned sorted for a stable order.
    """
    root = Path(root)
    match_full_path = "/" in pattern
    results = []

    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        # Prune in place so os.walk never descends into these.
        dirnames[:] = [
            d
            for d in dirnames
            if not d.startswith(".")
            and not os.path.islink(os.path.join(dirpath, d))
        ]

        for name in filenames:
            full = Path(dirpath) / name
            if full.is_symlink():
                continue
            subject = str(full.relative_to(root)) if match_full_path else name
            if fnmatch.fnmatch(subject, pattern):
                results.append(full)

    return sorted(results)
```

Two notes on the edges:

- `followlinks=False` stops `os.walk` from *descending* into symlinked directories, but they still show up in `dirnames`, which is why they're pruned explicitly. Without that, a symlinked dir yields a `(dirpath, [], [])` tuple you'd rather not see.
- Hidden *files* are not skipped — only hidden directories, as asked. If you want `.env` excluded too, add `if name.startswith("."): continue` at the top of the inner loop.
- `fnmatch.fnmatch` is case-insensitive on Windows and macOS-style filesystems. Swap in `fnmatch.fnmatchcase` if you need `*.PY` to stay distinct from `*.py` everywhere.
