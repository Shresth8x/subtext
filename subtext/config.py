"""Runtime configuration. No secrets in code — everything comes from env."""
from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # dotenv is optional; env vars may be set by the shell
    pass

ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = Path(os.getenv("SUBTEXT_CACHE_DIR", ROOT / "data" / "cache"))

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL = os.getenv("SUBTEXT_MODEL", "claude-opus-5")

# BSE blocks requests without a browser-shaped header set.
BSE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.bseindia.com/corporates/ann.html",
    "Origin": "https://www.bseindia.com",
    "Accept": "application/json, text/plain, */*",
}

# BSE rejects announcement windows wider than ~90 days, so we page in chunks.
BSE_WINDOW_DAYS = 80
BSE_PAGE_SIZE = 50
REQUEST_TIMEOUT = 40
POLITE_DELAY_SECONDS = 0.6
