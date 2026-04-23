from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.db.models import Stock, Price, TechnicalIndicator, Event

class StockService:
    @staticmethod
    async def get_stock(session: AsyncSession, symbol: str):
        result = await session.execute(select(Stock).where(Stock.symbol == symbol))
        return result.scalars().first()
    
    @staticmethod
    async def get_prices(session: AsyncSession, symbol: str, limit: int = 30):
        result = await session.execute(
            select(Price).where(Price.symbol == symbol).order_by(Price.date.desc()).limit(limit)
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_signals(session: AsyncSession, symbol: str, limit: int = 30):
        result = await session.execute(
            select(TechnicalIndicator).where(TechnicalIndicator.symbol == symbol).order_by(
                TechnicalIndicator.date.desc()).limit(limit)
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_events(session: AsyncSession, symbol: str, limit: int = 10, unresolved_only: bool = False):
        stmt = select(Event).where(Event.symbol == symbol)
        if unresolved_only:
            stmt = stmt.where(Event.resolved == False)

        stmt = stmt.order_by(Event.normalized_score.desc().nulls_last(), Event.start_date.desc()).limit(limit)

        result = await session.execute(stmt)
        return result.scalars().all()