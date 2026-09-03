```python
import os
from fnmatch import fnmatch
from pathlib import Path

PRUNED_DIRS = frozenset({"__pycache__", "node_modules"})


def find_files(root, pattern, pruned_dirs=PRUNED_DIRS, max_depth=None):
    """Return every file under `root` matching a glob `pattern`, sorted by path.

    A pattern with no slash is matched against the file name alone ("*.py").
    A pattern with a slash is matched against the path relative to `root`
    ("src/**/*.py"), where "**" spans any number of directory levels.

    `max_depth` limits how far below `root` the walk descends: 0 searches
    only `root` itself, 1 also searches its immediate subdirectories, and
    None (the default) is unlimited. A negative value searches nothing.

    Descent never crosses a symlink: directory entries are classified with
    `follow_symlinks=False`, so a symlinked directory is reported as a leaf
    and is not entered. Each real directory is also recorded by its
    (device, inode) identity and visited at most once, so a cycle built from
    bind mounts or hardlinked directories terminates instead of hanging.

    Hidden entries (a leading dot), symlinks, and directories named in
    `pruned_dirs` are skipped along with everything beneath them.
    """
    root = Path(root)
    whole_path_pattern = "/" in pattern or os.sep in pattern
    pattern_segments = pattern.replace(os.sep, "/").split("/")
    visited_dirs = set()
    matches = []

    def walk(directory, relative_segments, depth):
        if max_depth is not None and depth > max_depth:
            return
        try:
            stat = os.stat(directory, follow_symlinks=False)
            entries = list(os.scandir(directory))
        except OSError:
            return
        identity = (stat.st_dev, stat.st_ino)
        if identity in visited_dirs:
            return
        visited_dirs.add(identity)

        for entry in entries:
            if entry.name.startswith(".") or entry.is_symlink():
                continue
            segments = relative_segments + (entry.name,)
            if entry.is_dir(follow_symlinks=False):
                if entry.name not in pruned_dirs:
                    walk(entry.path, segments, depth + 1)
            elif entry.is_file(follow_symlinks=False):
                target = segments if whole_path_pattern else segments[-1:]
                if _segments_match(target, pattern_segments):
                    matches.append(Path(entry.path))

    walk(root, (), 0)
    matches.sort()
    return matches


def _segments_match(path_segments, pattern_segments):
    """Match path segments against pattern segments, honoring '**'."""
    if not pattern_segments:
        return not path_segments
    head, tail = pattern_segments[0], pattern_segments[1:]
    if head == "**":
        return any(
            _segments_match(path_segments[start:], tail)
            for start in range(len(path_segments) + 1)
        )
    return (
        bool(path_segments)
        and fnmatch(path_segments[0], head)
        and _segments_match(path_segments[1:], tail)
    )
```
