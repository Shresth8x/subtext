"""BSE corporate-filings client.

Everything here hits public, mandatory-disclosure endpoints. Responses and PDFs
are cached on disk so repeated runs don't re-hit BSE.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import time
from dataclasses import dataclass, asdict
from pathlib import Path

import requests

from . import config

ANN_URL = "https://api.bseindia.com/BseIndiaAPI/api/AnnSubCategoryGetData/w"
SEARCH_URL = "https://api.bseindia.com/BseIndiaAPI/api/PeerSmartSearch/w"
ATTACH_URL = "https://www.bseindia.com/xml-data/corpfiling/AttachLive/"

# An earnings-call transcript must look like a transcript AND like an earnings
# call. AGM / investor-day / analyst-meet transcripts are filed the same way and
# must be excluded or the quarter-on-quarter comparison is meaningless.
_TRANSCRIPT = re.compile(r"transcript", re.I)

# Banks and NBFCs file their quarterly earnings call under the BSE category
# "Analyst / Investor Meet - Outcome" rather than "Earnings Call Transcript" —
# SBI, Axis and Bajaj Finance all do. Treating an analyst/investor *meet* as a
# non-earnings event drops those companies entirely, so it counts here.
_EARNINGS = re.compile(
    r"earnings?\s*call|earning\s*call|con\s*call|conference\s*call|q[1-4]\s*fy"
    r"|analyst\s*/?\s*investor\s*meet|analyst\s*meet|investor\s*meet"
    r"|quarter|financial results", re.I)

# Only genuinely non-quarterly events. A multi-day strategy event or an AGM is
# not comparable quarter-on-quarter; a routine analyst meet is.
_EXCLUDE = re.compile(
    r"annual general meeting|\bagm\b|\begm\b|extra[- ]?ordinary general|"
    r"investor day|analyst day|capital markets day|\bai day\b|"
    r"investor conference|analyst conference|business responsibility",
    re.I,
)


@dataclass(frozen=True)
class Scrip:
    code: str
    name: str
    isin: str
    ticker: str


@dataclass(frozen=True)
class Filing:
    date: str            # ISO date, e.g. "2026-07-28"
    headline: str
    attachment: str      # PDF filename on BSE
    category: str
    scrip_code: str

    @property
    def url(self) -> str:
        return ATTACH_URL + self.attachment


def _cache_path(*parts: str) -> Path:
    p = config.CACHE_DIR.joinpath(*parts)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _get(url: str, params: dict | None = None, *, binary: bool = False):
    key = hashlib.sha1(f"{url}{sorted((params or {}).items())}".encode()).hexdigest()[:20]
    path = _cache_path("http", f"{key}.{'bin' if binary else 'json'}")
    if path.exists():
        return path.read_bytes() if binary else json.loads(path.read_text("utf-8"))

    time.sleep(config.POLITE_DELAY_SECONDS)
    r = requests.get(url, params=params, headers=config.BSE_HEADERS,
                     timeout=config.REQUEST_TIMEOUT)
    r.raise_for_status()
    if binary:
        path.write_bytes(r.content)
        return r.content
    path.write_text(r.text, "utf-8")
    return r.json()


_RESULT = re.compile(r"liclick\('(\d+)','([^']*)'\).*?<span>(.*?)</span>", re.S)


def _strip_tags(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>|&nbsp;", " ", s)).strip()


def resolve_ticker(ticker: str) -> Scrip:
    """NSE-style ticker -> BSE scrip code, via BSE's own search endpoint.

    BSE's search is fuzzy and ranks by relevance, not exactness: searching
    "MARUTI" returns MARUTI GLOBAL INDUSTRIES above Maruti Suzuki. Taking the
    first result therefore analyses the wrong company *silently*, which is far
    worse than failing. So every result is parsed and only an exact ticker match
    is accepted — ambiguity raises rather than guesses.
    """
    want = ticker.strip().upper()
    raw = _get(SEARCH_URL, {"Type": "SS", "text": want})
    html = raw if isinstance(raw, str) else str(raw)

    candidates: list[Scrip] = []
    for code, name, span in _RESULT.findall(html):
        parts = _strip_tags(span).split()
        if not parts:
            continue
        candidates.append(Scrip(
            code=code, name=name.strip(), ticker=parts[0].upper(),
            isin=next((p for p in parts if p.startswith("INE")), "")))

    if not candidates:
        raise LookupError(f"BSE search returned nothing for {ticker!r}")

    exact = [c for c in candidates if c.ticker == want]
    if not exact:
        near = ", ".join(f"{c.ticker} ({c.name[:22]})" for c in candidates[:4])
        raise LookupError(
            f"No BSE scrip has the exact ticker {want!r}. Closest: {near}. "
            f"Refusing to guess — the wrong company would be analysed silently.")
    return exact[0]


def announcements(scrip_code: str, *, months_back: int = 18) -> list[dict]:
    """All filings for a scrip, walked backwards in BSE-sized date windows."""
    today = dt.date.today()
    windows = max(1, round(months_back * 30 / config.BSE_WINDOW_DAYS))
    rows: list[dict] = []
    for i in range(windows):
        end = today - dt.timedelta(days=config.BSE_WINDOW_DAYS * i)
        start = today - dt.timedelta(days=config.BSE_WINDOW_DAYS * (i + 1))
        for page in range(1, 4):
            batch = _get(ANN_URL, {
                "pageno": page, "strCat": "-1", "subcategory": "-1",
                "strPrevDate": start.strftime("%Y%m%d"),
                "strToDate": end.strftime("%Y%m%d"),
                "strScrip": scrip_code, "strSearch": "P", "strType": "C",
            }).get("Table", [])
            rows.extend(batch)
            if len(batch) < config.BSE_PAGE_SIZE:
                break

    seen, unique = set(), []
    for r in rows:
        nid = r.get("NEWSID")
        if nid and nid not in seen:
            seen.add(nid)
            unique.append(r)
    return unique


def find_transcripts(scrip_code: str, *, months_back: int = 18) -> list[Filing]:
    """Earnings-call transcripts only, newest first."""
    out = []
    for r in announcements(scrip_code, months_back=months_back):
        # Positive matching reads every field, but exclusions are tested only
        # against NEWSSUB — the one genuinely categorical field. HEADLINE and
        # MORE are long free-text blurbs: Reliance's earnings-call filing
        # mentions its analyst meet in passing, and excluding on that text drops
        # a legitimate transcript.
        subject = str(r.get("NEWSSUB") or "")
        text = " ".join(str(r.get(f) or "") for f in ("NEWSSUB", "HEADLINE", "MORE"))
        attachment = (r.get("ATTACHMENTNAME") or "").strip()
        if not attachment.lower().endswith(".pdf"):
            continue
        if not _TRANSCRIPT.search(text) or _EXCLUDE.search(subject):
            continue
        if not _EARNINGS.search(text):
            continue
        out.append(Filing(
            date=(r.get("NEWS_DT") or "")[:10],
            headline=(r.get("NEWSSUB") or r.get("HEADLINE") or "").strip(),
            attachment=attachment,
            category=(r.get("CATEGORYNAME") or "").strip(),
            scrip_code=scrip_code,
        ))
    return sorted(out, key=lambda f: f.date, reverse=True)


def download(filing: Filing) -> Path:
    """Fetch the filing PDF into the cache and return its path.

    BSE serves recent attachments from AttachLive and older ones from AttachHis,
    with no flag in the announcement row saying which. Try both.
    """
    path = _cache_path("pdf", filing.scrip_code, filing.attachment)
    if path.exists() and path.stat().st_size > 0:
        return path

    last_error: Exception | None = None
    for base in (ATTACH_URL, ATTACH_URL.replace("AttachLive", "AttachHis")):
        try:
            data = _get(base + filing.attachment, binary=True)
        except requests.HTTPError as e:
            last_error = e
            continue
        if data.startswith(b"%PDF"):
            path.write_bytes(data)
            return path
        last_error = ValueError(f"{filing.attachment} is not a PDF (got {data[:16]!r})")
    raise ValueError(f"Could not download {filing.attachment}: {last_error}")


def filing_to_dict(f: Filing) -> dict:
    return asdict(f)


# Some companies (the Adani group, among others) satisfy the disclosure by filing
# a one-page cover letter that links to the transcript on their own website.
# Without following the link, those companies look like they never file at all.
_LINK_PDF = re.compile(r"https?://[^\s\"'<>]+?\.pdf", re.I)
COVER_LETTER_MAX_LINES = 200


def _looks_like_cover_letter(pdf: Path) -> bool:
    import pymupdf
    with pymupdf.open(pdf) as doc:
        if doc.page_count > 4:
            return False
        text = "\n".join(p.get_text() for p in doc)
    return len(text.splitlines()) < COVER_LETTER_MAX_LINES


def _extract_pdf_link(pdf: Path) -> str | None:
    """Prefer the PDF's own link annotations — the visible text wraps mid-URL."""
    import pymupdf
    with pymupdf.open(pdf) as doc:
        for page in doc:
            for link in page.get_links():
                uri = (link.get("uri") or "").strip()
                if uri.lower().endswith(".pdf"):
                    return uri
        # Fall back to rebuilding the URL from text with the line breaks removed.
        joined = re.sub(r"\s+", "", "\n".join(p.get_text() for p in doc))
    m = _LINK_PDF.search(joined)
    return m.group(0) if m else None


def fetch_transcript_pdf(filing: Filing) -> Path:
    """The actual transcript, following a cover-letter link when there is one."""
    path = download(filing)
    if not _looks_like_cover_letter(path):
        return path

    url = _extract_pdf_link(path)
    if not url:
        return path  # short document, but no link — let the parser judge it

    target = _cache_path("pdf", filing.scrip_code,
                         f"linked_{hashlib.sha1(url.encode()).hexdigest()[:16]}.pdf")
    if target.exists() and target.stat().st_size > 0:
        return target

    time.sleep(config.POLITE_DELAY_SECONDS)
    r = requests.get(url, headers={"User-Agent": config.BSE_HEADERS["User-Agent"]},
                     timeout=config.REQUEST_TIMEOUT)
    r.raise_for_status()
    if not r.content.startswith(b"%PDF"):
        return path
    target.write_bytes(r.content)
    return target
