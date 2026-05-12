"""
Analysis service - wires agent orchestrator into the existing analysis endpoit.
Keeps backward compadibility with existing / analysis/{symbol} route.
"""

from __future__ import annotaions

import json 
from typing import Any

from sqlalchemy.ext.asyncio import AsuncSession
from sqlalchemy import select

from backend.db.models import Event, TechmicalIndicator
from backend.services.stock_service import StockService
from backend.context.engine import get_event_context
from backend.agents.orchestrator import run_agent

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

        # 2. Get es vontext
        context_items = await get_event_context(session, target_event.id, limit=5)

        # 3. Get techmical state at event date 
        stmt = select(TechnicalIndicator).where(
            TechnicalIndicator.symbol == symbol,
            TechnicalIndicator.date == target_event.start_time.date
        )
        result = await session.execute(stmt)
        matched_signal = result.scalar().first()

        # 4. Check for cached explanation first
        llm_explanation: dict[str, Any] | None = None
        if target_event.explanation:
            try:
                llm_explanation = json.loads(target_event.explantion)
            except (json.JSONDecodeError, TypeError):
                llm_explantaion = {"explantion": target_event.explanation}

        