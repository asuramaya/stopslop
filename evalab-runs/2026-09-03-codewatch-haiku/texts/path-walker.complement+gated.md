```python
from pathlib import Path
from typing import List, Optional

def walk_glob(root_dir: str, pattern: str, exclude: Optional[List[str]] = None, max_depth: Optional[int] = None) -> List[str]:
    root = Path(root_dir)
    exclude = exclude or []
    matches = []
    visited = set()
    
    if not root.is_dir():
        return matches
    
    def visit(dirpath: Path, depth: int) -> None:
        if max_depth is not None and depth > max_depth:
            return
        
        try:
            real_path = dirpath.resolve()
        except (OSError, ValueError):
            return
        
        if real_path in visited:
            return
        visited.add(real_path)
        
        try:
            entries = dirpath.iterdir()
        except (OSError, PermissionError):
            return
        
        for entry in entries:
            if any(part.startswith('.') for part in entry.relative_to(root).parts):
                continue
            
            if entry.is_dir(follow_symlinks=True):
                visit(entry, depth + 1)
            elif entry.is_file(follow_symlinks=True) and entry.match(pattern):
                should_exclude = any(entry.match(p) for p in exclude)
                if not should_exclude:
                    try:
                        matches.append(str(entry.resolve()))
                    except (OSError, ValueError):
                        pass
    
    visit(root, 0)
    return sorted(set(matches))
```
