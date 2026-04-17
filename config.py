import os

# Request settings
REQUEST_TIMEOUT = 15
REQUEST_DELAY = 2.0  # seconds between requests

# Amazon base URL
AMAZON_BASE = "https://www.amazon.com"

# Best Seller categories: display name -> URL slug
BESTSELLER_CATEGORIES = {
    "all": "",
    "electronics": "electronics",
    "books": "books",
    "toys": "toys-and-games",
    "kitchen": "kitchen",
    "clothing": "apparel",
    "sports": "sporting-goods",
    "beauty": "beauty",
    "home": "home-garden",
}

# SQLite database path
DB_PATH = os.environ.get("TRACKER_DB", "tracker.db")

# Default monitor interval (minutes)
DEFAULT_INTERVAL = 60

# HTTP headers to mimic a real browser
BASE_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Cache-Control": "max-age=0",
}
