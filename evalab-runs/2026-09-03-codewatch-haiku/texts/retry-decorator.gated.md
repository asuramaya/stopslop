```python
import functools
import time
import random
from typing import Callable, TypeVar, Any

F = TypeVar('F', bound=Callable[..., Any])

def with_retries(max_attempts: int = 3, base_delay: float = 1.0, backoff_factor: float = 2.0) -> Callable[[F], F]:
    """Decorator that retries a function with exponential backoff and jitter on exception.
    
    Args:
        max_attempts: Maximum number of attempts before giving up.
        base_delay: Initial delay in seconds between retries.
        backoff_factor: Multiplier for delay after each failed attempt.
    
    Returns:
        A decorator that wraps the function with retry logic.
    
    Raises:
        The original exception if all attempts fail. KeyboardInterrupt and SystemExit are never retried.
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = base_delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except (KeyboardInterrupt, SystemExit):
                    raise
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts:
                        jittered_delay = delay * (0.5 + random.random())
                        print(f"Attempt {attempt} failed: {e}. Retrying in {jittered_delay:.2f}s...")
                        time.sleep(jittered_delay)
                        delay *= backoff_factor
                    else:
                        print(f"All {max_attempts} attempts failed.")
            
            raise last_exception
        
        return wrapper
    
    return decorator


# Example usage
@with_retries(max_attempts=3, base_delay=0.5, backoff_factor=2.0)
def unstable_operation():
    import random
    if random.random() < 0.7:
        raise ConnectionError("Network error")
    return "Success!"


if __name__ == "__main__":
    result = unstable_operation()
    print(result)
```
