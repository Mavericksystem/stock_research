import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.future import select
from backend.db.connection import async_session_maker
from backend.db.models import Stock, Price
from backend.ingestion.yfinance_client import fetch_stock_prices, fetch_stock_info

TARGET_SYMBOLS = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", 
            "META", "TSLA", "JPM", "V", "WMT"]
PERIOD = "2mo"

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
                stock = Stock(symbol=symbol, name=info.get("name", symbol), exchange=info.get("sector", "Unknown"))
                session.add(stock)
                await session.commit()
                await session.refresh(stock)
            else:
                print(f"stock {symbol } found in database.")
                stock.name = info.get("name", symbol)
                stock.exchange = info.get("sector", "Unknown")
                await session.commit()

            df = fetch_stock_prices(symbol, period=PERIOD)
            if df is None or df.empty:
                print(f"Warning: No valid price data for {symbol}.")
                continue

            existing_dates_stmt = select(Price.date).where(Price.symbol == stock.symbol)
            existing_dates_res = await session.execute(existing_dates_stmt)
            existing_dates = set(existing_dates_res.scalars().all())

            new_prices = []
            for date_obj, row in df.iterrows():
                if date_obj not in existing_dates:
                    new_price = Price(
                        symbol=stock.symbol,
                        date=date_obj,
                        open=row.get("open"),
                        high=row.get("high"),
                        low=row.get("low"),
                        close=row.get("close"),
                        volume=row.get("volume")
                    )
                    new_prices.append(new_price)

            if new_prices:
                session.add_all(new_prices)
                await session.commit()
                print(f"SUCCESS: Added {len(new_prices)} new price records for {symbol}.")
            else:
                print(f"INFO: Database is already up to date for {symbol}.")

if __name__ == "__main__":
    asyncio.run(ingest_market_data())