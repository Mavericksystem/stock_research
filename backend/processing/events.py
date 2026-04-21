import sys
import os 
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import select, and_, not_, exists
from sqlalchemy.ext.asyncio import async_sessionmaker

from backend.db.models import TecnicalIndicator, Event
from backend.db.connection import engine

sessionLocal = async_sessionmaker(engine, expire_on_commit=False)

SPIKE_THRESHOLD = 3.0
DROP_THRESHOLD = -3.0

async def detect_events(symbol: str, date: datetime, lookahead: int = 30):
    """Scan recent technical indicators for anomalies and create Event records."""

    cutoff_date = datetime.utcnow().date() - timedelta(days=days_lookback)

    async with sessionLocal() as session:
        # 1. Fetch recent signals for this symbol
        stmt = select(TechnicalIndicator).where(
            and_(
                TechnicalIndicator.symbol == symbol,
                TechnicalIndicator.date >= cutoff_date
            )
        ).order_by(TechnicalIndicator.date.asc())

        result = await session.execute(stmt)
        signals = result.scalars().all()

        if not signals:
            print(f"No recent signals found to scan for{symbol}")
            return
        events_created = 0

        # 2. Scan each days signal for anamalies
        for sig in signals:
            if sig.daily_return is None:
                continue

        daily_return = float(sig.daily_return)
        event_type = None

        if daily_return >= SPIKE_THRESHOLD:
            event_type = "PRICE_SPIKE"
        elif daily_return <= DROP_THRESHOLD:
            event_type = "PRICE_DROP"

            