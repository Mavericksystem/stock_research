from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.connection import get_db
from backend.services.analysis_service import AnalysisService
from backend.api.schemas import APIResponse, EventResponse, SignalResponse

router = APIRouter()

@router.get("/{symbol}/analysis", response_model=APIResponse)
async def analyze_stock(symbol: str, db: AsyncSession = Depends(get_db)):
    # Logic extracted clenly to service
    analysis_data = await AnalysisService.analyze_stock(session, symbol.upper())

    if "message" in analysis_data:
        return APIResponse(data=analysis_data)
    
    return APIResponse(data={
        "symbol": analysis_data["symbol"],
        "event_type": analysis_data["initial_insight"],
        "target_event": EventResponse.model_validate(analysis_data["target_event"]),
        "state_at_event": SignalResponse.model_validate(analysis_data["state_at_event"]),
        "llm_explanation": analysis_data["explanation"]
    }
)