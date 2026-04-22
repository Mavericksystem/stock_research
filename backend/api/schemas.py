from pydantic import BaseModel, ConfigDict
from typing import Any, Optional, Dict
from datetime import datetime, date

class Meta(BaseModel):
    timestamp: datetime = datetime.utcnow()
    version: str = "v1"

class APIResponse(BaseModel):
    status: str = "success"
    data: Any
    meta: Meta = Meta()

class APIErrorResponse(BaseModel):
    status: str = "error"
    error: Dict[str, str]
    meta: Meta = Meta()

class StockResponse(BaseModel):
    symbol: str
    name: Optional[str]
    exchange: Optional[str]
    is_active: bool
    model_config = ConfigDict(from_attributes=True)

class PriceResponse(BaseModel):
    date: date
    close: float
    adj_close: float
    volume: float
    model_config = ConfigDict(from_attributes=True)

class SignalResponse(BaseModel):
    date: date
    daily_return: Optional[float]
    sma_20: Optional[float]
    sma_50: Optional[float]
    rsi_14: Optional[float]
    volatility_20d: Optional[float]
    price_vs_sma_20: Optional[float]
    price_vs_sma_50: Optional[float]
    model_config = ConfigDict(from_attributes=True)

class EventResponse(BaseModel):
    date: date = None  # Using date to match DB
    start_date: date
    end_date: date
    event_type: str
    source: str
    magnitude: Optional[float]
    normalized_score: Optional[float]
    confidence: Optional[float]
    context: Optional[Dict[str, Any]]
    resolved: bool
    explanation: Optional[str]
    model_config = ConfigDict(from_attributes=True)