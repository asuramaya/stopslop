```python
import os
from pathlib import Path
from typing import List, Optional

def find_files_by_glob(root_dir: str, pattern: str, max_depth: Optional[int] = None) -> List[str]:
    """
    Recursively walk a directory tree and return all files matching a glob pattern.
    Skips hidden directories and symlinks. Prevents infinite loops from circular symlinks.
    
    Args:
        root_dir: Root directory to search from
        pattern: Glob pattern to match (e.g., '*.py', '**/*.txt')
        max_depth: Maximum directory depth to traverse (None for unlimited)
    
    Returns:
        Sorted list of absolute file paths matching the pattern
    
    Raises:
        ValueError: If root_dir does not exist or is not a directory
    """
    root_path = Path(root_dir).resolve()
    if not root_path.exists():
        raise ValueError(f"Directory does not exist: {root_dir}")
    if not root_path.is_dir():
        raise ValueError(f"Path is not a directory: {root_dir}")
    
    matching_files = []
    visited_inodes = set()
    
    for dirpath, dirnames, filenames in os.walk(root_path):
        depth = len(Path(dirpath).parts) - len(root_path.parts)
        
        dir_stat = os.stat(dirpath)
        inode = (dir_stat.st_ino, dir_stat.st_dev)
        
        if inode in visited_inodes:
            dirnames[:] = []
            continue
        visited_inodes.add(inode)
        
        if max_depth is None or depth < max_depth:
            dirnames[:] = [d for d in dirnames if not d.startswith('.') and not Path(dirpath, d).is_symlink()]
        else:
            dirnames[:] = []
        
        for filename in filenames:
            file_path = Path(dirpath, filename)
            if not file_path.is_symlink() and file_path.match(pattern):
                matching_files.append(str(file_path))
    
    return sorted(matching_files)
```
