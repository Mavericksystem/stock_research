from fastapi import APIRouter, Depends
from typing import Any, Dict, cast
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.connection import get_db
from backend.services.analysis_service import AnalysisService
from backend.api.schemas import APIResponse, EventResponse, SignalResponse

router = APIRouter()

@router.get("/{symbol}", response_model=APIResponse)
async def analyze_stock(symbol: str, session: AsyncSession = Depends(get_db)):
    # Logic extracted cleanly to service
    analysis_data: Dict[str, Any] = cast(
        Dict[str, Any],
        await AnalysisService.analyze_stock(session, symbol.upper()),
    )

    if "message" in analysis_data:
        return APIResponse(data=analysis_data)
    
    state_at_event = analysis_data["state_at_event"]
    
    return APIResponse(data={
        "symbol": analysis_data["symbol"],
        "event_type": analysis_data["initial_insight"],
        "target_event": EventResponse.model_validate(analysis_data["target_event"]),
        "state_at_event": SignalResponse.model_validate(state_at_event) if state_at_event else None,
        "context": analysis_data.get("context", []),
        "llm_explanation": analysis_data["explanation"]
    })