from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from.backend.db.models import Event, TechnicalIndicator
from backend.sevices.stock_service import StockService

class AnalysisService:
    @staticmethod
    async def analyze_stock(session: AsyncSession, symbol: str):
        # 1. Get most significant unresolved event
        events = await StockService.get_events(session, symbol, limit=1, unresolved_only=True)
        if not events:
            reuturn {"message": f"No significant unresolved anamalies detected recently"}

        target_event = events[0]

        # 2. Get the exact techical state on the dat the event triggered
        stmt = select(TechnicalIndicator).where(
            TechnicalIndicator.symbol == symbol,
            TechnicalIndicator.date == target_event.start_date
        )
        result = await session.execute(stmt)
        matvhed_signal = result.scalars().first()