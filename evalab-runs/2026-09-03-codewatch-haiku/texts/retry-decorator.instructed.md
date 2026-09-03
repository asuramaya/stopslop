```python
import time
import random
from functools import wraps

def with_retries(max_attempts=3, base_delay=1, max_delay=60, backoff_factor=2):
    """
    Decorator that retries a function on exception with exponential backoff and jitter.
    Does not retry on KeyboardInterrupt or SystemExit.
    
    Args:
        max_attempts: Maximum number of attempts (default: 3)
        base_delay: Initial delay in seconds (default: 1)
        max_delay: Maximum delay between retries (default: 60)
        backoff_factor: Multiplier for delay on each retry (default: 2)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = base_delay
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except (KeyboardInterrupt, SystemExit):
                    raise
                except Exception as e:
                    if attempt == max_attempts:
                        raise
                    
                    jittered_delay = delay * random.uniform(0.5, 1.0)
                    time.sleep(jittered_delay)
                    delay = min(delay * backoff_factor, max_delay)
        
        return wrapper
    return decorator


@with_retries(max_attempts=4, base_delay=0.5, backoff_factor=2)
def flaky_operation():
    import random
    if random.random() < 0.7:
        raise ConnectionError("Network timeout")
    return "success"
```
