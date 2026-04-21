from pydantic import BaseModel, ConfigDict
from typing import Any, Optional, List
from datetime import datetime

#generic response wrapper
class Meta(BaseModel):
    timestamp: datetime = datetime.utcnow()
    version: str = "v1"

class APIResponse(BaseModel):
    status: str = "success"
    meta: Meta = Meta()

# --- Domain Schema ===
class StockBase(BaseModel):
    symbol: str
    name: Optional[str]
    exchange: Optional[str]

class StockResponse(StockBase):
    is_active: bool
    model_config = ConfigDict(from_attributes=True)

