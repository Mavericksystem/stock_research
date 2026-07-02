"""
RSS poller — background task, not a request-driven endpoint.
 
Fetches a fixed list of finance RSS feeds on an interval, parses items,
and upserts into the existing `news` table (dedup on url via unique
constraint, same as news_scraper.upsert_news does for Finnhub/EDGAR).
 
No embeddings computed here — RSS items are for display/click-through
only, not for the RAG/event-linking pipeline. embedding stays NULL.
 
Runs as an asyncio background task started at FastAPI app startup.
Single task, single event loop — no Go, no worker pool needed at this
feed count/interval.
"""
from __future__ import annotations
 
import asyncio
import re
import logging
from datetime import datetime, timezone
from typing import Any
 
import feedparser
import httpx
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import async_sessionmaker
rom backend.db.connection import engine
from backend.db.models import News
 
# Reuse the same symbol->name map already used for entity scoring in
# news_scraper.py — keeps ticker filtering consistent across the codebase.
from backend.ingestion.news_scraper import SYMBOL_TO_NAME

logger = logging.getLogger(__name__)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

 Feed list. Add/remove freely — each is polled independently, one
# slow/dead feed doesn't block the others.
RSS_FEEDS: list[dict[str, str]] = [
    {"url": "https://feeds.content.dowjones.io/public/rss/RSSMarketsMain", "source": "WSJ Markets"},
    {"url": "https://www.cnbc.com/id/20910258/device/rss/rss.html", "source": "CNBC Markets"},
    {"url": "https://feeds.marketwatch.com/marketwatch/topstories/", "source": "MarketWatch"},
    {"url": "https://finance.yahoo.com/news/rssindex", "source": "Yahoo Finance"},
]

# Precompute lowercase match terms once — symbol + company name per ticker.
# e.g. "V" -> ["v", "visa"], "GOOGL" -> ["googl", "google"]
_TICKER_TERMS: dict[str, list[str]] = {
    sym: [sym.lower(), name.lower()] for sym, name in SYMBOL_TO_NAME.items()
}

_WORD_RE_CACHE: dict[str, "re.Pattern[str]"] = {}
 
 
def _match_symbol(title: str, summary: str) -> str | None:
    """Return the first tracked ticker mentioned in title/summary, else None.
 
    Ticker match is always word-boundary-only (case-sensitive on the raw
    text) — critical for short tickers like "V" or later additions like
    "T", where a raw lowercase substring check would match almost every
    article ("investors", "the", etc.). Company-name match is a safe
    substring check since names are multi-word/long enough not to false-hit.
    """

    
 
    raw_text = f"{title} {summary}"
    lower_text = raw_text.lower()

    for symbol, terms in _TICKER_TERMS.items():
        _, name_term = terms

        pattern = _WORD_RE_CACHE.setdefault(
            symbol, re.compile(rf"\b{re.escape(symbol)}\b")
        )
        if pattern.search(raw_text):
            return symbol

        if name_term and name_term in lower_text:
            return symbol

    return None
 
POLL_INTERVAL_SECONDS = 300  # 5 min — RSS feeds don't update faster than this anyway
FETCH_TIMEOUT_SECONDS = 15

def _parse_published(entry: dict[str, Any]) -> datetime:
    """feedparser gives a time.struct_time or nothing — normalize to UTC datetime."""
    for key in ("published_parsed", "updated_parsed"):
        st = entry.get(key)
        if st:
            return datetime(*st[:6], tzinfo=timezone.utc).replace(tzinfo=None)
    return datetime.utcnow()

async def _fetch_feed(client: httpx.AsyncClient, feed: dict[str, str]) -> list[dict[str, Any]]:
    """Fetch + parse one feed. Failures here are logged and swallowed —
    one bad feed must not kill the poll cycle for the other three."""
    try:
        resp = await client.get(feed["url"], timeout=FETCH_TIMEOUT_SECONDS)
        resp.raise_for_status()
    except Exception as e:
        logger.warning(f"[rss_poller] fetch failed for {feed['source']}: {e}")
        return []

    parsed = feedparser.parse(resp.content)
    if parsed.bozo:
        # bozo=True means the XML was malformed but feedparser did its best.
        # Still usable in most cases, just log it.
        logger.info(f"[rss_poller] {feed['source']} feed is malformed (bozo), parsing anyway")

    rows: list[dict[str, Any]] = []
    for entry in parsed.entries:
        url = entry.get("link")
        title = entry.get("title")
        if not url or not title:
            continue  # can't dedup or display without these — skip

        summary = entry.get("summary", "") or ""
        # Strip crude HTML tags feedparser sometimes leaves in summary
        import re
        summary = re.sub(r"<[^>]+>", "", summary).strip()[:500]

        title_clean = title.strip()
        matched_symbol = _match_symbol(title_clean, summary)
        if matched_symbol is None:
            continue  # not about any of the 10 tracked stocks — drop it

        rows.append(
            {
                "symbol": matched_symbol,
                "title": title_clean,
                "content": summary or None,
                "source": feed["source"],
                "url": url.strip(),
                "published_at": _parse_published(entry),
                "embedding": None,
                "embedding_model": None,
                "embedding_created_at": None,
            }
        )
    return rows

async def _upsert_rss_rows(rows: list[dict[str, Any]]) -> int:
    if not rows:
        return 0

    async with SessionLocal() as session:
        stmt = insert(News).values(rows)
        upsert_stmt = stmt.on_conflict_do_nothing(index_elements=["url"])
        result = await session.execute(upsert_stmt)
        await session.commit()
        return result.rowcount or 0

async def poll_once() -> None:
    """One full pass over all configured feeds."""