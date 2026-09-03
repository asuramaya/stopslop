```python
import time
import logging
import random
from functools import wraps

logger = logging.getLogger(__name__)


def with_retries(max_attempts=3, initial_delay=1, backoff_factor=2, exceptions=(Exception,)):
    """
    Decorator that retries a function with exponential backoff and jitter.
    
    Args:
        max_attempts: Maximum number of attempts (default: 3)
        initial_delay: Initial delay in seconds (default: 1)
        backoff_factor: Multiplier for delay after each attempt (default: 2)
        exceptions: Tuple of exceptions to catch (default: Exception)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except (KeyboardInterrupt, SystemExit):
                    raise
                except exceptions as e:
                    if attempt == max_attempts:
                        logger.error(
                            f"Failed after {max_attempts} attempts in {func.__name__}",
                            exc_info=True
                        )
                        raise
                    
                    sleep_time = random.uniform(0, delay)
                    logger.warning(
                        f"Attempt {attempt}/{max_attempts} failed in {func.__name__}: {e}. "
                        f"Retrying in {sleep_time:.2f}s..."
                    )
                    time.sleep(sleep_time)
                    delay *= backoff_factor
        
        return wrapper
    return decorator
```
