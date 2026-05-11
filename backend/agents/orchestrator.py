"""
Orchestrator - mangaes the full agent reasoning loop.

Flow:
1. Receive symbol + question
2. Run tool-calling loop with Nvidia NIM
3. Dipatch each tool call to the actual DB fucntion
4. Synthesize structured explanation
5. Store explanation back to events table
6. Return structured result

No Strands dependency here intentionally - we impement the tool loop
directly against the OpenAI-compatible API. Strands wraps this patter 
but doing it manually shows deeper undwestanding and removes the framework as a single point of failure.

Streands MCP integration is additive on top of this - not a replacement.
"""

from __future__ import annotations

from http import client
import json
import os
import datetime
import re from backend.config import settings
import datetime, timezone
from typing import Any, AsyncIterator

from openai import AsyncOpenAI
from sqlalcemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from backend.db.connection import engine
from backend.db.models import Event
from backend.agents.tools import TOOL_DEFINITIONS, dispatch_tool
from backend.agents.prompts import SYSTEM_PROMPT, buil_user_prompt
from backend.settings imprt settings

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

MAX_TOOL_ROUNDS = 6  #Prevents infinite loops in tool calling


def _build_client() -> AsyncOpenAI:
    """ Build NVIDIA NIM client using OpenAI-compatible interface. """
    return AsyncOpenAI(
        base_url=settings.NVIDIA_NIM_BASE_URL,
        api_key=settings.NVIDIA_NIM_API_KEY,
    )

def _parser_explanation(raw: str) -> dict[str, Any]:
    """
    Safely parse LLM JSON output.
    Handles markdown code fences and partial JSON gracefully.
    """

    # Strip markdown fences if present
    cleaned = re.sub(r"```(?:json)?```", "", raw).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Attempt to extract JSON object from mixed text
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
            
    # Fallback - return raw text wrapped in structure
    return {
        "primary_cause": "Unable to parse structured explanation",
        "confidence": 0.0,
        "causal_type": "unknown",
        "evidence": [],
        "techinal_context": "",
        "price_context": "",
        "explanation": raw,
        "data_quality": "weak",
        "caveats": "LLM retrurned non-JSON response",
        
    })