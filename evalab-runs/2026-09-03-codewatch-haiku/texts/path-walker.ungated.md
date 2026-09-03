```python
import os
from pathlib import Path
from typing import List, Set, Optional

def walk_and_glob(directory: str, pattern: str, max_depth: Optional[int] = None) -> List[str]:
    """Walk directory tree and return files matching glob pattern.
    
    Skips hidden dirs/files, symlinks, and circular symlink loops.
    
    Args:
        directory: Root directory to search
        pattern: Glob pattern (e.g., "*.py")
        max_depth: Maximum depth to traverse (None for unlimited)
    
    Returns:
        Sorted list of absolute file paths matching the pattern
    """
    root_path = Path(directory).resolve()
    if not root_path.is_dir():
        raise ValueError(f"Directory does not exist: {directory}")
    
    matches = []
    visited_inodes: Set[int] = set()
    
    for dirpath, dirnames, filenames in os.walk(root_path, followlinks=False):
        rel_path = Path(dirpath).relative_to(root_path)
        current_depth = len(rel_path.parts)
        
        if max_depth is not None and current_depth >= max_depth:
            dirnames[:] = []
        
        dirnames[:] = [d for d in dirnames if not d.startswith('.')]
        
        try:
            stat = os.stat(dirpath)
            dir_inode = (stat.st_dev, stat.st_ino)
            if dir_inode in visited_inodes:
                dirnames[:] = []
                continue
            visited_inodes.add(dir_inode)
        except (OSError, ValueError):
            continue
        
        for filename in filenames:
            if filename.startswith('.'):
                continue
            filepath = Path(dirpath) / filename
            if not filepath.is_symlink() and filepath.match(pattern):
                matches.append(str(filepath.absolute()))
    
    return sorted(matches)
```
