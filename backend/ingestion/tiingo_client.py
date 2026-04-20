import os 
import httpx
from datetime import datetime, timedelta

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.db.models import Stock, Price
from backend.db.connection import Base

load_dotenv()

TIINGO_API_KEY = os.getenv("TIINGO_API_KEY")
sessionLocal = async_sessionmaker(engine, expire_on_commit=False)

#fetching data from tiingo (async)
async def getch_tiingo(symbol: str, start_date: datetime, end_date: datetime):
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