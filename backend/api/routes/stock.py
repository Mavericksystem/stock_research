import asyncio
import json
from fastapi.responses import StreamingResponse
from backend.streaming.finnhub_ws import latest_prices, connection_state
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.connection import get_db
from backend.services.stock_service import StockService
from backend.api.schemas import APIResponse, APIErrorResponse, StockResponse, PriceResponse, SignalResponse, EventResponse

router = APIRouter()

@router.get("/stream")
async def stream_prices():
    """
    SSE endpoint for live price ticks.
 
    Snapshot cadence, not per-tick push: the Finnhub listener already
    coalesces ticks into `latest_prices` (last value per symbol wins),
    so this just re-emits that dict once a second. Simpler than a
    per-client queue and sufficient at 10 symbols / low client count —
    revisit only if that stops being true.
 
    Client usage:
        const es = new EventSource(`${API_BASE}/api/v1/stocks/stream`)
        es.onmessage = (e) => console.log(JSON.parse(e.data))
    """

    async def event_generator():
        while True:
            payload = {
                "prices": latest_prices,
                "connected": connection_state["connected"],
            }
            yield f"data: {json.dumps(payload)}\n\n"
            await asyncio.sleep(1)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )

@router.get("/{symbol}", response_model=APIResponse | APIErrorResponse)
async def get_stock_info(symbol: str, session: AsyncSession = Depends(get_db)):
    stock = await StockService.get_stock(session, symbol.upper())
    if not stock:
        return APIErrorResponse(error={"code": "NOT_FOUND", "message": f"Stock {symbol} not found"})
    return APIResponse(data={"stock": StockResponse.model_validate(stock)})

@router.get("/{symbol}/prices", response_model=APIResponse)
async def get_stock_prices(symbol: str, limit: int = Query(30, le=100), session: AsyncSession = Depends(get_db)):
    prices = await StockService.get_prices(session, symbol.upper(), limit)
    return APIResponse(data={"prices": [PriceResponse.model_validate(p) for p in prices]})

@router.get("/{symbol}/signals", response_model=APIResponse)
async def get_stock_signals(symbol: str, limit: int = Query(30, le=100), session: AsyncSession = Depends(get_db)):
    signals = await StockService.get_signals(session, symbol.upper(), limit)
    return APIResponse(data={"signals": [SignalResponse.model_validate(s) for s in signals]})

@router.get("/{symbol}/events", response_model=APIResponse)
async def get_stock_events(symbol: str, limit: int = Query(10, le=50), session: AsyncSession = Depends(get_db)):
    events = await StockService.get_events(session, symbol.upper(), limit=limit)
    return APIResponse(data=[EventResponse.model_validate(e) for e in events])

