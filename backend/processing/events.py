import sys
import os 
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import select, and_, not_, exists
from sqlalchemy.ext.asyncio import async_sessionmaker

from backend.db.models import TechnicalIndicator, Event
from backend.db.connection import engine

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

# Instead of a fixed 3%, we use Z-Score 2.0 (meaning a move > 2 standard deviations)
Z_THRESHOLD = 2.0

async def detect_events(symbol: str, days_lookback: int = 30):
    """Scan recent technical indicators for statistical anomalies and create Event records."""

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
        
        # 2. Batch fetch existing events to avoid N+1 query loop
        existing_stmt = select(Event.symbol, Event.start_date, Event.event_type).where(
            and_(
                Event.symbol == symbol,
                Event.start_date >= cutoff_date
            )
        )
        existing_result = await session.execute(existing_stmt)
        # Store as a set of tuples for O(1) lookup
        existing_events = set(existing_result.all())

        events_created = 0

        # 3. Scan each day's signal for statistical anomalies
        for sig in signals:
            if sig.daily_return is None or sig.volatility_20d is None:
                continue

            daily_return = float(sig.daily_return)
            volatility = float(sig.volatility_20d)

            # Avoid division by zero on flat stocks
            if volatility == 0:
                continue

            # Calculate the z-score (how many standard deviations was this move?)
            z_score = daily_return / volatility
            
            event_type = None

            if z_score >= Z_THRESHOLD:
                event_type = "PRICE_SPIKE"
            elif z_score <= -Z_THRESHOLD:
                event_type = "PRICE_DROP"

            # 4. If we found an anomaly, check our pre-fetched set 
            if event_type:
                key = (symbol, sig.date, event_type)
                
                # Check for existing
                if key in existing_events:
                    continue

                # 5. Determine trend context using our derived signals
                # If price_vs_sma_20 > 0, it means it closed above the 20-day trend.
                above_sma_20 = None
                if getattr(sig, 'price_vs_sma_20', None) is not None:
                     above_sma_20 = float(sig.price_vs_sma_20) > 0

                # 6. Insert new event
                new_event = Event(
                    symbol=symbol,
                    start_date=sig.date,
                    end_date=sig.date, # Single day event for now, can be expanded
                    event_type=event_type,
                    source="price",
                    magnitude=daily_return,
                    normalized_score=z_score,
                    confidence=0.90, # Placeholder until multi-signal validation exists
                    context={
                        "rsi": float(sig.rsi_14) if sig.rsi_14 else None,
                        "volatility": volatility,
                        "z_score": z_score,
                        "above_sma_20": above_sma_20
                    },
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
        import asyncio
        await asyncio.gather(*(detect_events(sym) for sym in symbols))

    asyncio.run(main())
