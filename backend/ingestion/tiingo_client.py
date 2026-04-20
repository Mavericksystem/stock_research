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

async def getch_tiingo(symbol: str, start_date: datetime, end_date: datetime):
    url = f"https://api.tiingo.com/tiingo/daily/{symbol}/prices"

    