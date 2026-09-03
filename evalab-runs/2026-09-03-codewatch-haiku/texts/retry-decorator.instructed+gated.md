```python
import time
import logging
import random
from functools import wraps
from typing import Callable, Any

logger = logging.getLogger(__name__)

def with_retries(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple = (Exception,)
):
    """
    Decorator that retries a function on exception with exponential backoff and jitter.
    Does not retry on KeyboardInterrupt or SystemExit.
    
    Args:
        max_attempts: Maximum number of attempts including the first
        base_delay: Initial delay in seconds before first retry
        max_delay: Maximum delay between retries in seconds
        exceptions: Tuple of exception types to catch and retry on
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            attempt = 1
            delay = base_delay
            
            while attempt <= max_attempts:
                try:
                    return func(*args, **kwargs)
                except (KeyboardInterrupt, SystemExit):
                    raise
                except exceptions as e:
                    if attempt == max_attempts:
                        logger.error(f"Failed after {max_attempts} attempts", exc_info=True)
                        raise
                    
                    jittered_delay = delay * random.uniform(0.5, 1.5)
                    jittered_delay = min(jittered_delay, max_delay)
                    logger.warning(f"Attempt {attempt}/{max_attempts} failed, retrying in {jittered_delay:.2f}s: {e}")
                    time.sleep(jittered_delay)
                    delay = min(delay * 2, max_delay)
                    attempt += 1
        
        return wrapper
    return decorator
```
