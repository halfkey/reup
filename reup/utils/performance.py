from typing import Callable, Any
import time
import functools
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)


@contextmanager
def timing(operation: str):
    """Context manager for timing operations."""
    start = time.perf_counter()
    yield
    elapsed = time.perf_counter() - start
    logger.debug(f"{operation} took {elapsed:.2f} seconds")


def performance_monitor(threshold: float = 1.0):
    """Decorator to monitor function performance."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start = time.perf_counter()
            result = func(*args, **kwargs)
            elapsed = time.perf_counter() - start

            if elapsed > threshold:
                logger.warning(
                    f"Performance warning: {func.__name__} took {elapsed:.2f} seconds"
                )
            return result

        return wrapper

    return decorator
