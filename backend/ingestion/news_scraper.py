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
        await session.execute(upsert_stmt)
        await session.commit()
        