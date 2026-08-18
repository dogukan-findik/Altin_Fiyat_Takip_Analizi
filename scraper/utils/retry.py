import time
import functools
from scraper.utils.logger import get_logger

logger = get_logger(__name__)

def retry(max_attempts: int = 3, base_delay_seconds: float = 2.0):
    """Exponential backoff ile retry decorator (dokümandaki Polly mantığının
    Python karşılığı — .NET tarafında HttpClient çağrıları Polly ile,
    scraper'daki HTTP/tarayıcı çağrıları bu decorator ile korunur)."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    last_exception = exc
                    if attempt == max_attempts:
                        break
                    delay = base_delay_seconds * (2 ** (attempt - 1))
                    logger.warning(
                        "Deneme %s/%s başarısız (%s), %.1fs sonra tekrar denenecek.",
                        attempt, max_attempts, exc, delay
                    )
                    time.sleep(delay)
            raise last_exception
        return wrapper
    return decorator
