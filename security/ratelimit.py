"""In-memory sliding-window rate limiter — best-effort, single-process."""
import time
from collections import defaultdict, deque
from threading import Lock

_buckets = defaultdict(deque)
_lock = Lock()


def hit(key: str, limit: int = 5, window_sec: int = 60) -> bool:
    """Return True if request is allowed, False if over the limit."""
    now = time.time()
    with _lock:
        q = _buckets[key]
        while q and (now - q[0]) > window_sec:
            q.popleft()
        if len(q) >= limit:
            return False
        q.append(now)
    return True
