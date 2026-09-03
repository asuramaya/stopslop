```python
from pathlib import Path
from typing import List, Union, Optional

def find_files_matching_glob(
    directory: Union[str, Path],
    glob_pattern: str,
    exclude_dirs: List[str] = None,
    max_depth: Optional[int] = None
) -> List[Path]:
    """Return sorted files matching glob, skipping hidden dirs, symlinks, and cycles."""
    root = Path(directory)
    
    if not root.is_dir():
        raise ValueError(f"{directory} is not a valid directory")
    
    if exclude_dirs is None:
        exclude_dirs = {'.git', '__pycache__', '.venv', 'node_modules'}
    else:
        exclude_dirs = set(exclude_dirs)
    
    matches = []
    visited = set()
    
    def traverse(current_dir: Path, depth: int) -> None:
        if max_depth is not None and depth > max_depth:
            return
        
        try:
            real_path = current_dir.resolve()
        except (OSError, RuntimeError):
            return
        
        if real_path in visited:
            return
        visited.add(real_path)
        
        try:
            for entry in current_dir.iterdir():
                if entry.is_symlink() or entry.name.startswith('.'):
                    continue
                if entry.name in exclude_dirs:
                    continue
                if entry.is_dir():
                    traverse(entry, depth + 1)
                elif entry.is_file() and entry.match(glob_pattern):
                    matches.append(entry)
        except (OSError, PermissionError):
            pass
    
    traverse(root, 0)
    return sorted(matches)
```
