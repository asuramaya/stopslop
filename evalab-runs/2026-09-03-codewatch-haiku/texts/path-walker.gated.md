```python
from pathlib import Path
from typing import List, Union, Set, Optional

def find_files(directory: Union[str, Path], pattern: str, max_depth: Optional[int] = None) -> List[Path]:
    """Walk directory tree, return files matching pattern. Skip symlinks and hidden dirs."""
    root = Path(directory).resolve()
    if not root.is_dir():
        raise ValueError(f"{directory} is not a valid directory")
    
    matching_files = []
    visited_inodes: Set[int] = set()
    
    def _walk(current_dir: Path, depth: int) -> None:
        if max_depth is not None and depth > max_depth:
            return
        
        if current_dir.is_symlink():
            return
        
        if any(part.startswith('.') for part in current_dir.relative_to(root).parts):
            return
        
        try:
            inode = (current_dir.stat().st_dev, current_dir.stat().st_ino)
            if inode in visited_inodes:
                return
            visited_inodes.add(inode)
        except OSError:
            return
        
        try:
            for item in current_dir.iterdir():
                if item.is_symlink() or any(p.startswith('.') for p in item.relative_to(root).parts):
                    continue
                if item.is_file() and item.match(pattern):
                    matching_files.append(item)
                elif item.is_dir():
                    _walk(item, depth + 1)
        except OSError:
            pass
    
    _walk(root, 0)
    return sorted(matching_files)
```
