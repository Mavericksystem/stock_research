from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.db.models import Stock, Prices, TechnicalIndicator, Event

class StockService:
    @staticmethod
    async def get_stock(session: AsyncSession, symbol: str):
        result = await session.execute(select(Stock).where(Stock.symbol == symbol))
        return result.scalars().first()
    
    @staticmethod
    async def get_prices(session: AsyncSession, symbol: str, limit: int = 30):
        result = await session.execute(
            select(Prices).where(Prices.symbol == symbol).order_by(Prices.date.desc()).limit(limit)
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_signals(session: AsyncSession, symbol: str, limit: int = 30):
        result = await session.execute(
            select(TechnicalIndicator).where(TechnicalIndicator.symbol == symbol).order_by(
                TechnicalIndicator.date.desc()).limit(limit)
        )
        return result.scalars().all()