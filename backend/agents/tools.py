""" 
Agent tools - pure async DB queries.
Each tools is a standalone function that the Strands agent can call.
No business logic here. Data retrieval only.
"""

from __future__ import annotations

import json
import inspect
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from backend.db.connection import engine
from backend.db.models import Event, News, EventNewsLink, Price, TechnicalIndicator

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

def _serialize(obj: Any) -> Any:
    """Make DB objects JSON-serializable for tool responses."""
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if hasattr(obj, "__dict__"):
        return {k: _serialize(v) for k, v in obj.__dict__.items() if not k.startswith("_")}
    return obj


# ____ Tool 1: Event detail

async def get_event_details(symbol: str, date_str: str | None = None) -> dict[str, Any]:
    """
    Fetch the most significant price event for a symbol.
    Optionally filter by date (YYYY-MM-DD).

    Returns event type, magnitude, z-score, RSI context,
    volatility context, and whether price was above SMA-20.
    
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
            "price_vs_sma_20": _f(indicator.price_vs_sma_20),
            "price_vs_sma_50": _f(indicator.price_vs_sma_50),
            "rsi_interpretation": (
                "overbought" if indicator.rsi_14 and float(indicator.rsi_14) > 70
                else "oversold" if indicator.rsi_14 and float(indicator.rsi_14) < 30
                else "neutral"
            ),
            "trend": (
                "above_both_smas" if (
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
        result = await session.execute(stmt)
        rows = result.all()

        if not rows:
            return {"found": False, "event_id": event_id, "articles": []}
        
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
        
    # --  Tools 4: Price History
async def get_price_history(symbol: str, around_date: str, days: int = 5) -> dict[str, Any]:
    """
    Fetch price history around an event date.
    Returns N days before and after the event date.
    Used to show price monentum vontext around the event.
    """
    async with SessionLocal() as session:
        try:
            center = date.fromisoformat(around_date)
        except ValueError:
            return {"found": False, "error": f"Invalid date: {around_date}"}
        
        from_dt = center - timedelta(days=days)
        to_dt = center + timedelta(days=days)

        stmt = (
            select(Price)
            .where(
                Price.symbol == symbol.upper(),
                Price.date >= from_dt,
                Price.date <= to_dt,
            )
            .order_by(Price.date.asc())
        )
        result = await session.execute(stmt)
        prices = result.scalars().all()

        if not prices:
            return {"found": False, "symbol": symbol, "around_date": around_date}
        
        def _f(val: Any) -> float | None:
            return float(val) if val is not None else None
        
        price_data = [
            {
                "date": p.date.isoformat(),
                "close": _f(p.adj_close) or _f(p.close),
                "volume": _f(p.volume),
                "is_event_date": p.date == center,
            }
            for p in prices
        ]

        return {
            "found": True,
            "symbol": symbol,
            "around_date": around_date,
            "prices": price_data,
        }
    

# ----- Tool registry - standard compatible tool definitions

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_event_details",
            "description": (
                "Get detaiils about a significant price event for a stock symbol."
                "Retruns event type (PRICE_SPIKE or PRICE_DROP), magnitude percentage,"
                "z-score, RSI, volatility, and trend context at the time of the event."
            ),
            "parameters":{
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock ticker symbol e.g. AAPL, MSFT, NVDA",
                    },
                    "date_str": {
                        "type": "string",
                        "description": "Optional date in YYYY-MM-DD format to filter by specific event date",
                    },
                },
                "required": ["symbol"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_technical_state",
            "description": (
                "Get technical indicators for a symbol on a date. "
                "Parameters: symbol (string) and date_str (YYYY-MM-DD string). "
                "Do NOT pass event_id to this tool."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock ticker symbol",
                    },
                    "date_str": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format",
                    },
                },
                "required": ["symbol", "date_str"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_news_context",
            "description": (
                "Get top ranked news articles linked to a specific event. "
                "Returns article titles, sources, publication times and relevance scores. "
                "Use this to identify the causal news catalyst for the price movement."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "event_id": {
                        "type": "integer",
                        "description": "The event ID from get_event_details",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of articles to return (default 5, max 10)",
                        "default": 5,
                    },
                },
                "required": ["event_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_price_history",
            "description": (
                "Get price history around an event date. "
                "Parameters: symbol (string), around_date (YYYY-MM-DD string), days (int optional). "
                "Do NOT pass start_date or end_date — only around_date."

            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock ticker symbol",
                    },
                    "around_date": {
                        "type": "string",
                        "description": "Center date in YYYY-MM-DD format",
                    },
                    "days": {
                        "type": "integer",
                        "description": "Days before and after the center date (default 5)",
                        "default": 5,
                    },
                },
                "required": ["symbol", "around_date"],
            },
        },
    },
]


# ------ Maps tool name to actual async function

TOOL_MAP: dict[str, Any] = {
    "get_event_details": get_event_details,
    "get_technical_state": get_technical_state,
    "get_news_context": get_news_context,
    "get_price_history": get_price_history,
}

async def dispatch_tool(tool_name: str, tool_args: dict[str, Any]) -> str:
    """
    Execute a tool call by name and return JSON string result.
    Called by the orchestrator after the LLM requests a tool.
    """
    fn = TOOL_MAP.get(tool_name)
    if not fn:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})

    # Normalize common argument aliases produced by models.
    if tool_name == "get_price_history":
        if "around_date" not in tool_args and "date_str" in tool_args:
            tool_args["around_date"] = tool_args.pop("date_str")

        # Some models attempt a start/end date range even though the tool only
        # accepts around_date (+ optional days). Normalize to avoid a failed
        # tool call followed by a retry.
        if "around_date" not in tool_args and ("start_date" in tool_args or "end_date" in tool_args):
            start_raw = tool_args.get("start_date")
            end_raw = tool_args.get("end_date")

            def _parse_iso_date(val: Any) -> date | None:
                if not isinstance(val, str):
                    return None
                try:
                    return date.fromisoformat(val)
                except ValueError:
                    return None

            start_dt = _parse_iso_date(start_raw)
            end_dt = _parse_iso_date(end_raw)

            if start_dt and end_dt and end_dt >= start_dt:
                span_days = (end_dt - start_dt).days
                center_dt = start_dt + timedelta(days=span_days // 2)
                tool_args["around_date"] = center_dt.isoformat()
                tool_args.setdefault("days", (span_days + 1) // 2)
            elif end_dt:
                tool_args["around_date"] = end_dt.isoformat()
            elif start_dt:
                tool_args["around_date"] = start_dt.isoformat()

            tool_args.pop("start_date", None)
            tool_args.pop("end_date", None)

    if tool_name == "get_technical_state":
        # Some models incorrectly pass only event_id. Resolve event_id to
        # the event's (symbol, start_date) so the tool call can succeed
        # without a costly fail-and-retry loop.
        if ("symbol" not in tool_args or "date_str" not in tool_args) and "event_id" in tool_args:
            try:
                event_id = int(tool_args["event_id"])
            except Exception:
                event_id = None

            if event_id is not None:
                async with SessionLocal() as session:
                    stmt = select(Event).where(Event.id == event_id).limit(1)
                    result = await session.execute(stmt)
                    event = result.scalars().first()

                if event:
                    tool_args.setdefault("symbol", event.symbol)
                    tool_args.setdefault("date_str", event.start_date.isoformat() if event.start_date else None)

    if tool_name == "get_news_context":
        # Some models may pass strings; coerce where safe.
        if "event_id" in tool_args:
            try:
                tool_args["event_id"] = int(tool_args["event_id"])
            except Exception:
                pass

    # Filter out unexpected kwargs so tool calls don't fail on minor schema drift.
    try:
        allowed = set(inspect.signature(fn).parameters.keys())
        tool_args = {k: v for k, v in tool_args.items() if k in allowed}
    except Exception:
        # If signature inspection fails for any reason, fall back to raw args.
        pass
    
    try: 
        result = await fn(**tool_args)
        return json.dumps(result, default=str)
    except Exception as e:
        return json.dumps({"error": f"Tool execution failed: {str(e)}"})