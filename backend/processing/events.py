import sys
import os 
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import select, and_, not_, exists
from sqlalchemy.ext.asyncio import async_sessionmaker

from backend.db.models import TechnicalIndicator, Event
from backend.db.connection import engine

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

SPIKE_THRESHOLD = 3.0
DROP_THRESHOLD = -3.0

async def detect_events(symbol: str, days_lookback: int = 30):
    """Scan recent technical indicators for anomalies and create Event records."""

    cutoff_date = datetime.utcnow().date() - timedelta(days=days_lookback)

    async with SessionLocal() as session:
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
            print(f"No recent signals found to scan for {symbol}")
            return
        events_created = 0

        # 2. Scan each days signal for anomalies
        for sig in signals:
            if sig.daily_return is None:
                continue

            daily_return = float(sig.daily_return)
            event_type = None

            if daily_return >= SPIKE_THRESHOLD:
                event_type = "PRICE_SPIKE"
            elif daily_return <= DROP_THRESHOLD:
                event_type = "PRICE_DROP"

            # 3. If we found an anomaly, check if we already recorded it 
            if event_type:
                # Check if this exact event type + date + symbol already exists
                exists_stmt = select(exists().where(
                    and_(
                        Event.symbol == symbol,
                        Event.date == sig.date,
                        Event.event_type == event_type
                    )
                ))

                already_exists = await session.scalar(exists_stmt)

                # 4. If new. inser it into the events table
                if not already_exists:
                    new_event = Event(
                        symbol=symbol,
                        date=sig.date,
                        event_type=event_type,
                        magnitude=sig.daily_return,
                        context={"rsi_at_time": float(sig.rsi_14) if sig.rsi_14 else None,
                                 "volatility_at_time": float(sig.volatility_20d) if sig.volatility_20d else None},
                        resolved=False,
                        explanation=None
                    )
                    session.add(new_event)
                    events_created += 1
                    
        if events_created > 0:
            await session.commit()
            print(f"[{symbol}] Created {events_created} new events.")
        else:
            print(f"[{symbol}] No new events detected.")

if __name__ == "__main__":
    import asyncio
    
    async def main():
        symbols = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "JPM", "V", "WMT"]
        for sym in symbols:
            await detect_events(sym)

    asyncio.run(main())
