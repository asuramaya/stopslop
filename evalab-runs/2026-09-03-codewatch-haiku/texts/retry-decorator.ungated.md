```python
import time
import random
import functools


def with_retries(max_attempts=3, base_delay=1, backoff_factor=2, exceptions=(Exception,)):
    """
    Decorator to retry a function on exception with exponential backoff and jitter.
    
    Re-executes the decorated function up to max_attempts times if an exception
    is raised. Between attempts, waits for an exponentially increasing duration
    with random jitter to prevent synchronization of retries across instances.
    Uses full jitter: delay between 0 and (base_delay * backoff_factor^attempt).
    
    KeyboardInterrupt and SystemExit are never retried and are raised immediately.
    
    Args:
        max_attempts: Maximum number of attempts (default: 3)
        base_delay: Initial delay in seconds (default: 1)
        backoff_factor: Multiplier for exponential backoff (default: 2)
        exceptions: Tuple of exception types to catch (default: (Exception,))
    
    Raises:
        The last exception if all attempts fail.
    
    Example:
        @with_retries(max_attempts=5, base_delay=0.5)
        def unstable_operation():
            return some_risky_call()
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except (KeyboardInterrupt, SystemExit):
                    raise
                except exceptions as e:
                    if attempt == max_attempts - 1:
                        raise
                    delay = base_delay * (backoff_factor ** attempt)
                    time.sleep(random.uniform(0, delay))
        
        return wrapper
    
    return decorator
```
