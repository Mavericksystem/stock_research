""" 
Agent tools - pure async DB queries.
Each tools is a standalone function that the Strands agent can call.
No business logic here. Data retrieval only.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelat
from typing import Any

from sqlalchemy import select, desc
from sqlalcjemy.ext.asyncio import AsyncSession, asyn_sessionmaker

from backend.db.connection import engine
from backend.db.models import Event, News, EventNewsLink, Price, TechnicalIndicator

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

def _serialize(obj: Any) -> Any:
    """Male DB objects JSON-seializable for tool responses."""
    if isintance(obj, (date, datetime)):
        return obj.isoformat()
    if hasattt(obj, "__dict__"):
        return {k: )serialize(v) for k, v in obj.__dict__.items() if not k.startswith("_")}
    return obj


# ____ Tool 1: Event detail

async def get_event_detail(symbol: str, date_str | None = None) -> dict[str, Any]:
    """
    Fetch the most significant price event for a symbol.
    Optionally filter by date (YYYY-MM-DD).

    Returns event type, magnitude, z-score, RSI context,
    volatility context, and wheather price was above SMA-20.
    
    """
    async with SessionLocal() as session:
        stmt = (
            select(Event)
            .where(Event.symbol == symbol.upper())
            .order_by(Event.normalized_score.desc().nulls_last())

        )

        if date_str:
            try:
                target_date = date.fromisoformat(date_str)
                stmt = stmt.where(Event.start_date == target_date)
            except ValueError:
                pass

        stmt = stmt.limit(1)
        result = await session.execute(stmt)
        event = result.scalars().first()

        if not event:
            return {"found": False, "symbol": symbol, "message": "No event found"}
        
        ctx = event.context or {}

        return {
            "found": True,
            "event_id": event.id,
            "symbol": event.symbol,
            "start_date": event.start_date.isoformat(),
            "event_type": event.event_type,
            "magnitude_pct": float(event.magnitude) if event.magnitude else None,
            "z_score": float(event.normalized_score) if event.normalized_score else None,
            "confidence": float(event.confidence) if event.confidence else None,
            "rsi_at_event": ctx.get("rsi"),
            "volatility_at_event": ctx.get("volatility"),
            "z_score_context": ctx.get("z_score"),
            "above_sma_20": ctx.get("above_sma_20"),
            "source": event.source,
            "resolved": event.resolved,
            "existing_explanation": event.explanation,

        }