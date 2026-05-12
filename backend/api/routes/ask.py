"""
POST /api/v1/ask - Natural language question aswering over market evetns.
GET /api/v1/ask/stream - Streaming version.
"""

from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.agents.orchestrator import run_agent, stream_agent
from backend.api.schemas import APIErrorResponse, APIErrorResponse

router = APIRouter()

class AskRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=5
        max_length=500,
        description="Natural language question about a stock movement",
        examples=["Why did visaa spike on April 29?"]
    )

    symbol: str = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Stock ticker symbol, e.g. AAPL",
        examples=["AAPL", "TSLA", "GOOG"]
        )
    
    