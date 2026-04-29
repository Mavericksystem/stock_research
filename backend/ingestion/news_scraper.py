import os
import sys
from datetime import datetime, timedelta, date, timezone
from typing import Any, cast

import httpx
from dotenv import load_dotenv
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
from backend.db.connection import engine
from backend.db.models import News, Event, EventNewsLink

load_dotenv()
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def fetch_finnhub_news(symbol: str, from_date: date, to_date: date) -> list[dict[str, Any]]:
    if not FINNHUB_API_KEY:
        raise ValueError("FINNHUB_API_KEY not set")
    url = "https://finnhub.io/api/v1/company-news"
    params = {
        "symbol": symbol,
        "from": from_date.isoformat(),
        "to": to_date.isoformat(),
        "token": FINNHUB_API_KEY,

    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.get(url, params=params)
        r.raise_for_status()
        data = r.json()
        if not isinstance(data, list):
            return []
        return cast(list[dict[str, Any]], data)
    
def transform_finnhub_news(rows: list[dict[str, Any]], symbol: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in rows:
        ts = item.get("datetime")
        published_at = None
        if ts:
            published_at = datetime.fromtimestamp(int(ts), tz=timezone.utc).replace(tzinfo=None)

        transformed: dict[str, Any] = {
            "symbol": symbol,
            "title": item.get("headline"),
            "content": item.get("summary"),
            "source": item.get("source") or "finnhub",
            "url": item.get("url"),
            "published_at": published_at,
        }
        out.append(transformed)

    return [x for x in out if x.get("url") and x.get("published_at")]
    
async def upsert_news(news_rows: list[dict[str, Any]]) -> None:
    if not news_rows:
        return 
    
    async with SessionLocal() as session:
        stmt = insert(News).values(news_rows)

        upsert_stmt = stmt.on_conflict_do_nothing(index_elements=["url"])
        await session.execute(upsert_stmt)
        await session.commit()
    
STRONG_KEYWORDS = [
    "earnings", "revenue", "profit", "guidance",
    "downgrade", "upgrade", "rating",
    "acquisition", "merger",
    "lawsuit", "sec", "investigation",
]

WEAK_KEYWORDS = [
    "ai", "stock", "market", "investment",
    "crypto", "portfolio"
]

NEGATIVE_KEYWORDS = [
    "crypto", "bitcoin", "etf", "macro", "inflation"
]

def time_score(event_date: date, published_at: datetime) -> float:
    days = abs((published_at.date() - event_date).days)
    if days == 0:
        return 1.0
    elif days == 1:
        return 0.7
    elif days == 2:
        return 0.4
    else:
        return 0.0

def title_score(title: str | None) -> float:
    t = (title or "").lower()
    score = 0.0
    for w in STRONG_KEYWORDS:
        if w in t:
            score += 1.0
    for w in WEAK_KEYWORDS:
        if w in t:
            score += 0.2
    return min(score, 2.0)

def entity_score(title: str | None, symbol: str) -> float:
    t = (title or "").lower()
    if symbol.lower() in t:
        return 1.0
    return 0.3

def penalty(title: str | None) -> float:
    t = (title or "").lower()
    for w in NEGATIVE_KEYWORDS:
        if w in t:
            return -0.5
    return 0.0

def relevance_score_v2(event_dt: date, published_at: datetime, title: str | None, symbol: str) -> float:
    t_score = time_score(event_dt, published_at)
    title_s = title_score(title)
    entity_s = entity_score(title, symbol)
    p = penalty(title)

    final = (t_score * 0.5) + (title_s * 0.3) + (entity_s * 0.2) + p
    return float(round(final, 4))

async def link_event_to_news(event_id: int, symbol: str, window_days: int = 2, limit: int = 50) -> int:
    async with SessionLocal() as session:
        event = await session.get(Event, event_id)
        if not event:
            return 0
        
        center = cast(date, event.start_date)
        start = datetime.combine(center - timedelta(days=window_days), datetime.min.time())
        end = datetime.combine(center + timedelta(days=window_days), datetime.max.time())

        news_q = (
            select(News)
            .where(News.symbol == symbol, News.published_at >= start, News.published_at <= end)
            .order_by(News.published_at.desc())
            .limit(limit)
        )
        res = await session.execute(news_q)
        candidates = res.scalars().all()

        if not candidates:
            return 0
        
        link_rows: list[dict[str, Any]] = []
        for n in candidates:
            score = relevance_score_v2(
                center,
                cast(datetime, n.published_at),
                cast(str | None, n.title),
                symbol
            )
            if score >= 0.8:
                link_rows.append(
                    {
                        "event_id": event_id,
                        "news_id": n.id,
                        "relevance_score": score,
                    }
                )

        if not link_rows:
            return 0

        # Sort by score descending and keep only the top 7 highest-signal articles
        link_rows.sort(key=lambda x: x["relevance_score"], reverse=True)
        link_rows = link_rows[:7]

        stmt = insert(EventNewsLink).values(link_rows)

        stmt = stmt.on_conflict_do_update(
            constraint="uix_event_news_link",
            set_={
                "relevance_score": stmt.excluded.relevance_score,
            },
        )

        await session.execute(stmt)
        await session.commit()
        return len(link_rows)
    
async def run_context_for_symbol(symbol: str, days_back: int = 7):
    to_dt = datetime.now(timezone.utc).date()
    from_dt = to_dt - timedelta(days=days_back)

    data = await fetch_finnhub_news(symbol, from_dt, to_dt)
    rows = transform_finnhub_news(data, symbol)
    await upsert_news(rows)
    
    async with SessionLocal() as session:
        ev_q = (
            select(Event)
            .where(Event.symbol == symbol, Event.resolved == False)
            .order_by(Event.start_date.desc())
            .limit(20)
        )
        res = await session.execute(ev_q)
        events = res.scalars().all()

    for e in events:
        await link_event_to_news(cast(int, e.id), symbol)

if __name__ == "__main__":
    import asyncio

    async def main():
        for sym in ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", 
            "META", "TSLA", "JPM", "V", "WMT"]:
            await run_context_for_symbol(sym, days_back=10)

    asyncio.run(main())