import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.future import select
from baackend.db.connection import async_session_maker
from backend.db.models import Stock, Price
from backend.ingestion.yfinance_client import fetch_stock_prices, fetch_stock_info

TARGET_SYMBOLS = ["AAPL", "TSLA", "MSFT"]
PERIOD = "1mo"

async def ingest_market_data ():
    print(f"starting ingestion pipeline for : {', '.join(TARGET_SYMBOLS)}")

    async with async_session_maker() as session:
        for symbol in TARGET_SYMBOLS:
            print(f"\n--- Processing {symbol} ---")

            info = fetch_stock_info(symbol)

            stmt = select(Stock).where(Stock.symbol == symbol)
            result = await session.execute(stmt)
            stock = result.scalars().first()

            if not stock:
                print(f"Adding new stock: {symbol} to database.")
                stock = stock(symbol=symbol, name=info["name"], sector=info["sector"])
                session.add(stock)
                await session.commit()
                await session.refresh(stock)
            else:
                print(f"stock {symbol } found in database.")
                stock.name = info["name"]
                stock.sector = info["sector"]
                await session.commit()

            