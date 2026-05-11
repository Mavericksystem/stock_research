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
    
# ____ Tool 2: Technical State

async def get_technical_state(symbol: str, date_str: str) -> dict[str, Any]:
    """
    Fetch exact technical indicator state for a symbol on a specific date.
    Returns RSI, SMA20, SMA50, daily return, volatility, price vs SMA.
    Used to characterize the market condition at the moment of the event.
    """
    async with SessionLocal() as session:
        try: 
            target_date = date.fromisoformat(date_str)
        except ValueError:
            return {"found": False, "error": f"Invalid date format: {date_str}"}
        
        stmt = select(TechnicalIndicator).where(
            TechnicalIndicator.symbol == symbol.upper(),
            TechnicalIndicator.date == target_date,

        )
        result = await session.execute(stmt)
        indicator = result.scalars().first()

        if not indicator:
            return {"found": False, "symbol": symbol, "date": date_str}
        
        def _f(val: Any) -> float | None:
            return float(val) if val is not None else None
        
        return {
            "found": True,
            "symbol": symbol,
            "date": date_str,
            "daily_return_pct": _f(indicator.daily_return),
            "return_7d_pct": _f(indicator.return_7d),
            "rsi_14": _f(indicator.rsi_14),
            "sma_20": _f(indicator.sma_20),
            "sma_50": _f(indicator.sma_50),
            "volatility_20d": _f(indicator.volatility_20d),
            "price_vs_sma_20d": _f(indicator.price_vs_sma_20d),
            "price_vs_sma_50": _f(indicator.price_vs_sma_50),
            "rsi_interpretation": (
                "overbought" if indicator.rsi_14 and float(indicator.rsi_14) > 70
                else "oversold" if indicator.rsi_14 and float(indicator.rsi_14) < 30
                else "neutral"
            ),
            "trend": (
                "above_both_sma" if (
                    indicator.price_vs_sma_20 and float(indicator.price_vs_sma_20) > 0
                    and indicator.price_vs_sma_50 and float(indicator.price_vs_sma_50) > 0
                )
                else "below_both_smas" if (
                    indicator.price_vs_sma_20 and float(indicator.price_vs_sma_20) < 0
                    and indicator.price_vs_sma_50 and float(indicator.price_vs_sma_50) < 0

                )
                else "mixed"
                ),
        }
    
    # ----  Tool 3: News Context

    async def get_news_context(event_id: int, limit: int = 5) -> dict[str, Any]:
        """
        Fetch top ranked news articles linkded to a specific evetn.
        Returns titles, sources, publication timestamps, relevance scores.
        and URLs. Orderd By relevance score descending.
        This is the primary caussal evidence layer.
        """
        async with SessionLocal() as session:
            stmt = (
                select(
                    News.id,
                    News.title,
                    News.source,
                    News.url,
                    News.published_at,
                    News.content,
                    EventNewsLink.relevance_score,
                )
                .join(EventNewsLink, EventNewsLink.news_id == News.id)
                .where(EventNewsLink.event_id == event_id)
                .order_by(desc(EventNewsLink.relevance_score), desc(News.published_at))
                .limit(limit)
            )
            result = await sesssion.execute(stmt)
            rows = result.all()

            if not rows:
                return{"found": False, "event_id": event_id, "articles": []}
            
            articles = []
            for r in rows:
                # Truncate content for token efficiency - first 300 chars enough for context
                content_preview = (r.content or "")[:300].strip() if r.content else None

                articles.append({
                    "news_id": r.id,
                    "title": r.title,
                    "source": r.source,
                    "url": r.url,
                    "published_at": r.published_at.isoformat() if r.published_at else None,
                    "relevance_score": float(r.relevance_score) if r.relevance_score else None,
                    "content_preview": content_preview,
                })

            return {
                "found": True,
                "event_id": event_id,
                "article_count": len(articles),
                "articles": articles,
            }