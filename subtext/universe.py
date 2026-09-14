"""Index constituents, straight from NSE's own published lists.

Hardcoding a ticker list rots — constituents change every six months. These CSVs
are the official source, so the universe stays current on its own.
"""
from __future__ import annotations

import csv
import io

import requests

from . import config

CSV_URL = "https://niftyindices.com/IndexConstituent/ind_nifty{n}list.csv"
SIZES = (50, 100, 200, 500)


def nifty(n: int = 100, *, refresh: bool = False) -> list[str]:
    """NSE symbols for the Nifty `n`, cached on disk."""
    if n not in SIZES:
        raise ValueError(f"Nifty size must be one of {SIZES}, got {n}")

    cache = config.CACHE_DIR / "universe" / f"nifty{n}.csv"
    if cache.exists() and not refresh:
        text = cache.read_text("utf-8")
    else:
        r = requests.get(CSV_URL.format(n=n),
                         headers={"User-Agent": config.BSE_HEADERS["User-Agent"]},
                         timeout=config.REQUEST_TIMEOUT)
        r.raise_for_status()
        text = r.text
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(text, "utf-8")

    rows = csv.DictReader(io.StringIO(text))
    return [row["Symbol"].strip() for row in rows if row.get("Symbol", "").strip()]
