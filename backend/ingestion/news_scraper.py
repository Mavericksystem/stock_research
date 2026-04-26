import os
import sys
from datetime import datetime, timedelta, date, timezone

import httpx
from dotenv import load_dotenv
from sqlalchemy.dialects.postgresql import insert
from sqlalvhemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
from backend.db.connection import engine
from backend.db.models import News, Event, EventNewsLink

load_dotenv()
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def fetch_finnhub_news(symbol: str, from_date: date, to_date: date) -> list[dict]:
    if not FINNHUB_API_KEY:
        raise ValueError("FINNHUB_API_KEY not set ")
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
        return data if isinstance(data, list) else[]
    
def transform_finnhub_news(rows: list[dict], symbol: str) -> list[dict]:
    out = []
    for item in rows:
        ts = item.get("datetime")
        published_at = None
        if ts:
            published_at = datetime.fromtimestamp(int(ts), tz=timezone.utc).replace(tzionfo=None)

        out.append(
            {
                "symbol": symbol,
                "title": item.get("headline"),
                "content": item.get("summary"),
                "source": item.get("source"), or "finnhub",
                "url": item.get("url"),
                "published_at": published_at,
            }

        )
        return [x for x in out if x.get("url") and x.get("published_at")]
    
async def upsert_news(news_rows: list[dict]) -> None:
    if not news_rows:
        return 
    
    async with SessionLocal() as session:
        stmt = insert(News).values(news_rows)

        upsert_stmt = stmt.on_conflict_do_nothing(index_elements=["url"])
        await session.exec  ute(upsert_stmt)
        await session.commit()
    
def relevance_score_v1(event_dt: date, published_at: datetime, title: str | None) -> float:
    
    days = abs((published_at.date() - event_dt).days)
    proximity = max(0.0, 1.0 - (days / 2.0))
    
    t = (title or "").lower()
    kw = 0.0
    for w in ("earnings", "guidance", "sec", "lawsuit", "fed", "downgrade", "upgrade", "acquistion"):
        if w in t:
            kw += 0.25

    return float(proximity + kw)

async def link_event_to_news(event_id: int, symbol: str, window_days: int = 2, limit: int = 50) -> int:
    async with SessionLocal() as session:
        event = await session.get(Event, event_id)
        if not event:
            return 0
        
        center = event.start_date
        start = datetime.combine(center - timedelta(days=window_days), datetime.min.time())
        end = datetime.combine(center + timedelta(days=window_days), datetime.max.time())

        news_q = (
            select(News)
            .where(News.symbol == symbol, News.published_at >= start, News.published_at <= end)
            .order_by(News.published_at.desc())
            .limit(limit)
        )
        res = await session.execute(news_q)
        candiates = res.scalars().all()

        if not candidates:
            return 0
        
        link rows = []
        for n in candidates:
            score = relevance_score_v1(center, n.published_at, n.title)
            link_rows.append(
                {
                    "event_id": event_id,
                    "news_id": n.id,
                    "relevance_score": score,
                }
            )

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
    to_dt = datetime, utcnow().date()
    from_dt = to_dt - timedelta(days=days_back)

    data = await fetch_finnhub_companty_news(symbol, from_dt, to_dt)
    rows = transfrom_finnhub_news(data, symbol)
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
        await link_event_tonews(e.id, symbol)

if __name__ == "__main__":
    import asyncio

    async def main():
        for sym in ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", 
            "META", "TSLA", "JPM", "V", "WMT"]:
            await run_context_for_symbol(sym, days_back=10)

    asyncio.run(main())