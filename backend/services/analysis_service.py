"""Analysis service.

Wires the agent orchestrator into the existing analysis endpoint.
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.context.engine import get_event_context
from backend.db.models import TechnicalIndicator
from backend.services.stock_service import StockService


class AnalysisService:

    @staticmethod
    async def analyze_stock(session: AsyncSession, symbol: str) -> dict[str, Any]:
        """
        Full analysis pipeline for a symbol.

        1. Find most significant unresolved event
        2. Get technical state at event time
        3. Get linked news context 
        4. Run agent to generate LLM explanation
        5. Return structured analysis result
        
        If event already has a stored explantion, return it
        without re-running the agent (cache behavior).
        """

        # 1. Get most significant unresolved event
        events = await StockService.get_events(
            session, symbol, limit=1, unresolved_only=True
        )
        if not events:
            return {"message": f"No significant unresolved anomalies detected for {symbol}"}
        target_event = events[0]

        # 2. Get event context
        context_items = await get_event_context(session, target_event.id, limit=5)

        # 3. Get technical state at event date
        stmt = select(TechnicalIndicator).where(
            TechnicalIndicator.symbol == symbol,
            TechnicalIndicator.date == target_event.start_date,
        )
        result = await session.execute(stmt)
        matched_signal = result.scalars().first()

        # 4. Check for cached explanation first
        llm_explanation: dict[str, Any] | None = None
        if target_event.explanation:
            try:
                llm_explanation = json.loads(target_event.explanation)
            except (json.JSONDecodeError, TypeError):
                llm_explanation = {"explanation": target_event.explanation}

        # 5. Run agent if no cached explanation
        if llm_explanation is None:
            try:
                # Lazy import so the API can boot even if the agent stack
                # has optional deps or is temporarily broken.
                from backend.agents.orchestrator import run_agent  # type: ignore

                agent_result = await run_agent(
                    symbol=symbol,
                    question=f"Why did {symbol} stock move significantly on {target_event.start_date}?"
                )
                llm_explanation = agent_result.get("explanation", agent_result)
            except Exception as e:
                llm_explanation = {
                    "explanation": f"Agent unavailable: {str(e)}",
                    "confidence": 0.0,
                    "data_quality": "weak",
                }

        return {
            "symbol": symbol,
            "target_event": target_event,
            "state_at_event": matched_signal,
            "explanation": llm_explanation,
            "context": context_items,
        }