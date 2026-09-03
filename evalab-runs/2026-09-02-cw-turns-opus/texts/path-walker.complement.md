```python
import fnmatch
import logging
import os

log = logging.getLogger(__name__)


def walk_glob(root, pattern, skip_dirs=None, max_depth=None):
    """Return sorted paths under `root` whose base name matches `pattern`.

    Hidden entries (leading dot) and symlinks are skipped, along with any
    directory named in `skip_dirs`. Every directory is visited at most
    once: a bind mount or a hardlinked directory can make the same inode
    reachable by two paths, which would otherwise recurse without end.

    `max_depth` counts directory levels below `root`, so 0 matches only
    files sitting directly in `root` and None means no limit.
    """
    if skip_dirs is None:
        skip_dirs = {".git", "__pycache__", "node_modules"}
    else:
        skip_dirs = set(skip_dirs)

    seen = set()
    matches = []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        try:
            info = os.stat(dirpath)
        except OSError as exc:
            log.warning("skipping %s: %s", dirpath, exc)
            dirnames[:] = []
            continue

        key = (info.st_dev, info.st_ino)
        if key in seen:
            log.warning("skipping %s: already visited this directory", dirpath)
            dirnames[:] = []
            continue
        seen.add(key)

        rel = os.path.relpath(dirpath, root)
        depth = 0 if rel == os.curdir else rel.count(os.sep) + 1

        if max_depth is not None and depth >= max_depth:
            dirnames[:] = []
        else:
            dirnames[:] = [
                d
                for d in dirnames
                if d not in skip_dirs
                and not d.startswith(".")
                and not os.path.islink(os.path.join(dirpath, d))
            ]

        for name in filenames:
            if name.startswith(".") or not fnmatch.fnmatch(name, pattern):
                continue
            full = os.path.join(dirpath, name)
            try:
                if os.path.islink(full) or not os.path.isfile(full):
                    continue
            except OSError as exc:
                # The tree can change under a long walk; a vanished or
                # unreadable entry is not a match, so move on.
                log.warning("skipping %s: %s", full, exc)
                continue
            matches.append(full)

    matches.sort()
    return matches
```
