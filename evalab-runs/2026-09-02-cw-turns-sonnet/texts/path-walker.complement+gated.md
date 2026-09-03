```python
import fnmatch
import os
from collections.abc import Iterator


def find_matching_files(
    root_dir: str, pattern: str, max_depth: int | None = None
) -> Iterator[str]:
    visited_dirs: set[tuple[int, int]] = set()

    def resolve_dir_key(path: str) -> tuple[int, int] | None:
        try:
            st = os.stat(path)
        except OSError:
            return None
        return (st.st_dev, st.st_ino)

    root_dir = os.path.normpath(root_dir)
    root_depth = root_dir.count(os.sep)
    root_key = resolve_dir_key(root_dir)
    if root_key is not None:
        visited_dirs.add(root_key)

    matches = []
    for dirpath, dirnames, filenames in os.walk(root_dir, followlinks=True):
        depth = dirpath.count(os.sep) - root_depth
        if max_depth is not None and depth >= max_depth:
            dirnames[:] = []
            continue

        kept = []
        for d in dirnames:
            full = os.path.join(dirpath, d)
            if d.startswith("."):
                continue
            if os.path.islink(full):
                key = resolve_dir_key(full)
                if key is None or key in visited_dirs:
                    continue
                visited_dirs.add(key)
            kept.append(d)
        dirnames[:] = kept

        for filename in filenames:
            full_path = os.path.join(dirpath, filename)
            if os.path.islink(full_path):
                continue
            if fnmatch.fnmatch(filename, pattern):
                matches.append(full_path)

    return iter(sorted(matches))
```
