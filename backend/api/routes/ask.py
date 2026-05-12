"""
POST /api/v1/ask - Natural language question aswering over market evetns.
GET /api/v1/ask/stream - Streaming version.
"""

from __future__ import annotations
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.agents.orchestrator import run_agent, stream_agent
from backend.api.schemas import APIErrorResponse, APIErrorResponse, APIResponse

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
    
class AskStremsRequest(BaseModel):
    question: str = Field(..., min_length=5, max_length=500)
    symbol: str = Field(..., min_length=1, max_length=10)

@router.post("", response_model=APIResponse)
async def ask(request: AskRequest):
    """
    Answer a natural language question about a stock price movement.
    
    The agent will:
    1. Detect the most significant evetn for the symbol 
    2. Retrieve technical indicators at the evetn time 
    3. Pull ranked causal news context
    4. Synthesize a structured explanation

    Returns a structured JSON explanation with confidence score,
    causal type classification, and supporting evidence.
    """
    

@router.post("/stream")
async def ask_stream(request: AskStreamRequest):
    """
    Streaming version of /ask.
    Returns Server=Sent Events (SSE).
    Tool calls run first, then explanation streams token by token.

    Client usage:
    const es = new EventSource('/api/v1/ask/stream')
    es.onmessage = (e) => console.log(JSON.parse(e.data))
    """
    try:
        return StreamingResponse(
            stream_agent(
                symbol=request.symbol,
                question=request.question
            ),
            media_type="text/event-stream"
            headers={
                "Cache-Contrrol": "no-cache",
                "x-Accel-Buffering": "no",
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Stream agent failed: {str(e)}",
        )