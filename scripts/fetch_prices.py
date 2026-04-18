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
