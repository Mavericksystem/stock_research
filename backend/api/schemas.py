from pydantic import BaseModel, ConfigDict
from typing import Any, Optional, Dict
from datetime import datetime, date

class Meta(BaseModel):
    timestamp: datetime = datetime.utcnow()
    version: str = "v1"

class APIResponse(BaseModel):
    status: str = "success"
    data: Any = None
    meta: Meta = Meta()

class APIErrorResponse(BaseModel):
    status: str = "error"
    error: Dict[str, str]
    meta: Meta = Meta()

class StockResponse(BaseModel):
    symbol: str
    name: Optional[str] = None
    exchange: Optional[str] = None
    is_active: bool = True
    model_config = ConfigDict(from_attributes=True)

class PriceResponse(BaseModel):
    date: date
    close: float
    adj_close: float
    volume: float
    model_config = ConfigDict(from_attributes=True)

class SignalResponse(BaseModel):
    date: date
    daily_return: Optional[float] = None
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    rsi_14: Optional[float] = None
    volatility_20d: Optional[float] = None
    price_vs_sma_20: Optional[float] = None
    price_vs_sma_50: Optional[float] = None
    model_config = ConfigDict(from_attributes=True)

class EventResponse(BaseModel):
    start_date: date
    end_date: date
    event_type: str
    source: str
    magnitude: Optional[float] = None
    normalized_score: Optional[float] = None
    confidence: Optional[float] = None
    context: Optional[Dict[str, Any]] = None
    resolved: bool = False
    explanation: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class ContextItemResponse(VaseModel):
    title: Optional[str] = None
    source: Optional[str] = None
    url: Optional[str] = None
    published_at: Optional[datetime] = None
    relecvance_scroe: Oprional[float] = None