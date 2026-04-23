from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.db.models import Event, TechnicalIndicator
from backend.services.stock_service import StockService

class AnalysisService:
    @staticmethod
    async def analyze_stock(session: AsyncSession, symbol: str):
        # 1. Get most significant unresolved event
        events = await StockService.get_events(session, symbol, limit=1, unresolved_only=True)
        if not events:
            return {"message": f"No significant unresolved anomalies detected recently"}

        target_event = events[0]

        # 2. Get the exact techical state on the dat the event triggered
        stmt = select(TechnicalIndicator).where(
            TechnicalIndicator.symbol == symbol,
            TechnicalIndicator.date == target_event.start_date
        )
        result = await session.execute(stmt)
        matched_signal = result.scalars().first()

        # 3. Base Intelligence Generation
        insight = "Neutral"
        if matched_signal:
            if matched_signal.rsi_14 and float(matched_signal.rsi_14) > 70:
                insight = "Technically overbought during event."
            elif matched_signal.rsi_14 and float(matched_signal.rsi_14) < 30:
                insight = "Technically oversold during event."
        
        return {
            "symbol": symbol,
            "target_event": target_event,
            "state_at_event": matched_signal,
            "initial_insight": insight,
            "explanation": target_event.explanation
        }