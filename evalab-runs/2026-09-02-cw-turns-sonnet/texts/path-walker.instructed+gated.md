```python
import fnmatch
import os
from pathlib import Path


def find_files(
    root: str, pattern: str, max_depth: int | None = None
) -> list[Path]:
    root_path = Path(root)
    matches = []
    seen_dirs = set()
    stack = [(root_path, 0)]
    while stack:
        current, depth = stack.pop()
        real = current.resolve()
        if real in seen_dirs:
            continue
        seen_dirs.add(real)
        try:
            entries = list(current.iterdir())
        except OSError:
            continue
        for entry in entries:
            if entry.name.startswith("."):
                continue
            if entry.is_symlink():
                continue
            if entry.is_dir():
                if max_depth is None or depth < max_depth:
                    stack.append((entry, depth + 1))
            elif fnmatch.fnmatch(entry.name, pattern):
                matches.append(entry)
    return sorted(matches)
```
