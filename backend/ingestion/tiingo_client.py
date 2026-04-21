import os 
import httpx
from datetime import datetime, timedelta

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select

import sys
# Ensure project root is on sys.path so `import backend...` works when running this file directly
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.db.models import Stock, Price
from backend.db.connection import engine

load_dotenv()

TIINGO_API_KEY = os.getenv("TIINGO_API_KEY")
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

#fetching data from tiingo (async)
async def fetch_tiingo(symbol: str, start_date: str, end_date: str):
    url = f"https://api.tiingo.com/tiingo/daily/{symbol}/prices"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Token {TIINGO_API_KEY}"
    }

    params = {
        "startDate": start_date,
        "endDate": end_date
    }

    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=headers, params=params, timeout=20.0)
        r.raise_for_status()
        return r.json()
    
#transform tiingo data to match our db schema
def transform(data: list, symbol: str) -> list[dict]:
    rows = []
    for d in data:
        rows.append({
            "symbol": symbol,
            "date": datetime.fromisoformat(d["date"].replace("Z", "+00:00")).date(),
            "open": d.get("open"),
            "high": d.get("high"),
            "low": d.get("low"),
            "close": d.get("close"),
            "volume": d.get("volume"),

            "adj_open": d.get("adjOpen"),
            "adj_high": d.get("adjHigh"),
            "adj_low": d.get("adjLow"),
            "adj_close": d.get("adjClose"),

            "div_cash": d.get("divCash"),
            "split_factor": d.get("splitFactor"),

        })
    return rows


#Ensure stock exacts (foreign key setup)
async def ensure_stock_exists(symbol: str):
    """ensure the parent stock record exists before insering price."""
    async with SessionLocal() as session:
        result = await session.execute(select(Stock).where(Stock.symbol == symbol))
        stock = result.scalars().first()

        if not stock:
            new_stock = Stock(symbol=symbol, name=symbol, exchange="Unknown")
            session.add(new_stock)
            await session.commit()
            print(f"Created parent stock reccord: {symbol}")

#upsert into db
async def upsert_prices(rows: list[dict]):
    if not rows:
        return
    
    async with SessionLocal() as session:
        stmt = insert(Price).values(rows)

        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=["symbol", "date"],
            set_={
                "open": stmt.excluded.open,
                "high": stmt.excluded.high,
                "low": stmt.excluded.low,
                "close": stmt.excluded.close,
                "volume": stmt.excluded.volume,

                "adj_open": stmt.excluded.adj_open,
                "adj_high": stmt.excluded.adj_high,
                "adj_low": stmt.excluded.adj_low,
                "adj_close": stmt.excluded.adj_close,

                "div_cash": stmt.excluded.div_cash,
                "split_factor": stmt.excluded.split_factor,
            }
        )
        await session.execute(upsert_stmt)
        await session.commit()

#main pipeline function
async def run(symbol: str):
    await ensure_stock_exists(symbol)

    end = datetime.utcnow().date()
    start = end - timedelta(days=365)

    print(f"Fetching {symbol} from {start} to {end}")

    data = await fetch_tiingo(symbol, start.isoformat(), end.isoformat())

    if not data:
        print("No daily price data returned from tiingo")
        return
    
    rows = transform(data, symbol)
    print(f"Transformed {len(rows)} rows for insertion")

    await upsert_prices(rows)
    print("Ingestion complete")

if __name__ == "__main__":
    import asyncio
    
    async def main():
        top_10_stocks = [
            "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", 
            "META", "TSLA", "JPM", "V", "WMT"
        ]
        for symbol in top_10_stocks:
            try:
                await run(symbol)
            except Exception as e:
                print(f"Error processing {symbol}: {e}")
                
    asyncio.run(main())