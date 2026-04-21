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
