```python
import fnmatch
import os
from pathlib import Path


def find_matching_files(root, pattern, max_depth=None):
    root_path = Path(root)
    root_depth = len(root_path.parts)
    matches = []
    seen_dirs = set()
    for dirpath, dirnames, filenames in os.walk(root_path, followlinks=True):
        depth = len(Path(dirpath).parts) - root_depth
        if max_depth is not None and depth >= max_depth:
            dirnames[:] = []
            continue
        real_dir = os.path.realpath(dirpath)
        if real_dir in seen_dirs:
            dirnames[:] = []
            continue
        seen_dirs.add(real_dir)
        dirnames[:] = [d for d in dirnames if not d.startswith('.')]
        for filename in filenames:
            file_path = Path(dirpath) / filename
            if file_path.is_symlink():
                continue
            if fnmatch.fnmatch(filename, pattern):
                matches.append(file_path)
    return sorted(matches)
```
