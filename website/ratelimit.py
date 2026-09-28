from django.core.cache import cache
from django.utils import timezone


def get_client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def is_rate_limited(key, limit, window_seconds):
    """Fixed-window counter backed by the shared DB cache, so it's correct
    across gunicorn workers and Cloud Run instances. Fails open if the cache
    itself is unavailable, so a cache outage never blocks real traffic.
    """
    now = int(timezone.now().timestamp())
    window = now // window_seconds
    cache_key = f"ratelimit:{key}:{window}"
    try:
        try:
            count = cache.incr(cache_key)
        except ValueError:
            cache.set(cache_key, 1, timeout=window_seconds + 5)
            count = 1
    except Exception:
        return False
    return count > limit
