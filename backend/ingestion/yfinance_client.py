import yfinance as yf
import pandas as pd
from typing import Optional

def fetch_stock_prices(symbol: str, period: str = "1mo") -> Optional[pd.DataFrame]:
    """
    Ftches historical daily proces for a given stock symbol using yfinance.
    period can be "1mo", "6mo", "max", etc.
    """
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history

        if df.empty:
            print(f"No data found for symbol: {symbol}")
            return None
        
        df.index = pd.to_datetime(df.index).date
        df.index.name = "date"

        df.columns = [c.lower() for c in df.columns]

        column_to_keep = ["open", "high", "low", "close", "volume"]
        df = df[[c for c in column_to_keep if c in df.columns]]

        return df
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None
    
def fetch_stock_info(symbol: str) -> dict:
    """
    fetches basic info (name, sector) for a stock.
    """
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        return {
            "symbol": symbol,
            "name": info.get("shortName", symbol)
            "sector": info.get("sector", "Unknown")
        }