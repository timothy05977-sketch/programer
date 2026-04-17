import random
import time
import requests
from config import BASE_HEADERS, REQUEST_TIMEOUT, REQUEST_DELAY

# Rotating user agents to reduce chance of blocks
_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]

_last_request_time = 0.0


def get(url: str, session: requests.Session | None = None) -> requests.Response:
    """Fetch URL with rate limiting and a random user agent."""
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < REQUEST_DELAY:
        time.sleep(REQUEST_DELAY - elapsed)

    headers = {**BASE_HEADERS, "User-Agent": random.choice(_USER_AGENTS)}
    requester = session or requests
    resp = requester.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
    _last_request_time = time.time()
    resp.raise_for_status()
    return resp


def new_session() -> requests.Session:
    s = requests.Session()
    return s
