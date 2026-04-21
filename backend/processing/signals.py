import sys
import os 
import pandas as pd
import pandas_ta as ta
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.dialects.postgresql import insert

sys.path.append(os.path.dirname(os.dirname(os.path.abspath(__file__))))

from backend.db.connection import engine

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def compute_signal(symbol: str):
    """fetch prices, compute signals via pandas_ta, and upsert to database"""
    async with SessionLocal
