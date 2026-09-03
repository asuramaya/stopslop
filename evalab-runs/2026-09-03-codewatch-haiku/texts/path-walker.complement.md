```python
import os
from pathlib import Path
from typing import List, Optional

def glob_files(directory: str, pattern: str, 
               absolute: bool = True,
               max_depth: Optional[int] = None) -> List[Path]:
    """Walk directory tree returning files matching glob, following symlinks
    but detecting cycles. Skips hidden files and symlinks."""
    
    root = Path(directory).resolve()
    if not root.is_dir():
        raise ValueError(f"Directory not found: {directory}")
    
    matches = []
    visited = set()
    
    try:
        for dirpath, dirnames, filenames in os.walk(root, followlinks=True):
            dirpath_obj = Path(dirpath)
            
            if max_depth is not None:
                depth = len(dirpath_obj.relative_to(root).parts)
                if depth >= max_depth:
                    dirnames.clear()
            
            try:
                stat = dirpath_obj.stat()
                inode = (stat.st_dev, stat.st_ino)
                if inode in visited:
                    dirnames.clear()
                    continue
                visited.add(inode)
            except (OSError, PermissionError):
                dirnames.clear()
                continue
            
            dirnames[:] = [d for d in dirnames 
                          if not d.startswith('.') and 
                          not (dirpath_obj / d).is_symlink()]
            
            for filename in filenames:
                if not filename.startswith('.'):
                    file_path = dirpath_obj / filename
                    if not file_path.is_symlink() and file_path.match(pattern):
                        matches.append(file_path if absolute 
                                      else file_path.relative_to(root))
    except PermissionError as e:
        raise PermissionError(f"Permission denied accessing {directory}") from e
    
    return sorted(matches)
```
