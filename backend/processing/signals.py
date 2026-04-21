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
    async with SessionLocal() as session:
        #1. fetch prices from db
        stmt = select(Prices).where(Price.symbol == symbol).order_by(Price.data.asc())
        result = await session.execute(stmt)
        prices = result.scalars().all()

        if not prices:
            print(f"No prices found for {symbil}")
            return 
        
        #2. Convert to Dataframe
        data = [{
            "date": p.date,
            "cose": float(p.adj_close) if p.adj_close is not None else float(p.close)
        } for p in prices]

        df = pd.DataFrame(data)
        df.set_index("date", inplace=True)

        