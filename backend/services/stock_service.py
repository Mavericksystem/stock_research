from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.db.models import Stock, Prices, TechnicalIndicator, Event

class StockService:
    @staticmethod
    async def get_stock(session: AsyncSession, symbol: str):
        result = await session.execute(select(Stock).where(Stock.symbol == symbol))
        return result.scalars().first()
    
    