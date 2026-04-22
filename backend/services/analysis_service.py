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