```python
import functools
import time
import random
from typing import TypeVar, Callable, Any, Type, Tuple

F = TypeVar('F', bound=Callable[..., Any])

def with_retries(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
) -> Callable[[F], F]:
    """
    Decorator to retry a function on exception with exponential backoff and jitter.
    
    Args:
        max_attempts: Maximum number of attempts (must be >= 1)
        base_delay: Initial delay in seconds between retries
        max_delay: Maximum delay cap in seconds
        exceptions: Tuple of exception types to catch and retry on
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except (KeyboardInterrupt, SystemExit):
                    raise
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                        delay += random.uniform(0, delay * 0.1)
                        time.sleep(delay)
            
            raise last_exception
        return wrapper
    return decorator
```
