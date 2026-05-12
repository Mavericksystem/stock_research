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
from backend.agents.prompts import SYSTEM_PROMPT, buil_user_prompt, build_user_prompt
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

async def _store_explanation(event_id: int, explanation_json: dict[str, Any]) -> None:
    """
    Persist explanation  back to events table.
    Stores full JSON as string in events.explanation column.
    Marks event as resolved.
    """

    async with SessionLocal() as session:
        event = await session.get(Event, event_id)
        if not event:
            return
        
        event.explanation = json.dumps(explanation_json)
        event.resolved = True
        await session.commit()

async def run_agent(
        symbol: str, 
        question: str,
) -> dict[str, Any]:
    """
    Main agent entry point.
    
    Runs the full tool-calling loop:
    1. Send system + user prompt to NIVIDIA NIM
    2. If midel requests tool calls, dispatch them
    3. Feed results back to model
    4. Repeat untill model returns final answer
    5. Parse and store structured explanation
    6. Return to API layer
    
    Returns structured explanation dict.
    """
    client = _build_client()
    symbol = symbol.upper()

    # Build initial message history
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_prompt(symbol, question)},
    ]

    tool_round = 0
    tool_call_log: list[dict[str, Any]] = []
    event_id: int | None = None

    # Agent loop - continues untill model stops calling tool

    while tool_round < MAX_TOOL_ROUNDS:
        response = await client.chat.completions.create(
            model =settings.BaseSettings,
            messages = messages,
            tool=TOOL_DEFINITIONS,
            tool_choice="auto",
            temperature=settings.AGENT_TEMPERATURE,
            max_tokens=settings.AGENT_MAX_TOKENS,
            top_p=settings.AGENT_TOP_P,
        )

        choice = response.choices[0]
        message = choice.message

        # A