from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.connection import get_db
from backend.services.stock_service import StockService
from backend.api.schemas import APIResponse, StockResponsse, PriceResponse, SignalResponse, EventResponse

router = APIRouter()

@router.get("/{symbol}", response_model=APIResponse)
async def get_stock_info(symbol: str, db: AsyncSession = Depends(get_db)):
    stock = await StockService.get_stock(db, symbol.upper())
    if not stock:
        return APIResponse(error={"code": "NOT_FOUND", "message": f"Stock {symbol} not found"})
    return APIResponse(data={"stock": StockResponse.model_validate(stock)})
