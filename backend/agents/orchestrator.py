"""Orchestrator - manages the full agent reasoning loop.

Flow:
1. Receive symbol + question
2. Run tool-calling loop with Nvidia NIM
3. Dispatch each tool call to the actual DB function
4. Synthesize structured explanation
5. Store explanation back to events table
6. Return structured result

No Strands dependency here intentionally - we implement the tool loop
directly against the OpenAI-compatible API. Strands wraps this pattern
but doing it manually shows deeper understanding and removes the framework as a single point of failure.

Strands MCP integration is additive on top of this - not a replacement.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, AsyncIterator

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import async_sessionmaker

from backend.agents.prompts import SYSTEM_PROMPT, build_user_prompt
from backend.agents.tools import TOOL_DEFINITIONS, dispatch_tool
from backend.config.settings import settings
from backend.db.connection import engine
from backend.db.models import Event

logger = logging.getLogger(__name__)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

MAX_TOOL_ROUNDS = 6  # Prevents infinite loops in tool calling


def _build_client() -> AsyncOpenAI:
    """Build NVIDIA NIM client using OpenAI-compatible interface."""
    return AsyncOpenAI(
        base_url=settings.NVIDIA_NIM_BASE_URL,
        api_key=settings.NVIDIA_NIM_API_KEY,
    )


def _parse_explanation(raw: str) -> dict[str, Any]:
    """
    Safely parse LLM JSON output.
    Handles markdown code fences and partial JSON gracefully.
    """
    import re

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
        "technical_context": "",
        "price_context": "",
        "explanation": raw,
        "data_quality": "weak",
        "caveats": "LLM returned non-JSON response",
    }


async def _store_explanation(
    event_id: int, explanation_json: dict[str, Any]
) -> None:
    """
    Persist explanation back to events table.
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
    1. Send system + user prompt to NVIDIA NIM
    2. If model requests tool calls, dispatch them
    3. Feed results back to model
    4. Repeat until model returns final answer
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

    # Agent loop - continues until model stops calling tools
    while tool_round < MAX_TOOL_ROUNDS:
        response = await client.chat.completions.create(
            model=settings.NVIDIA_NIM_MODEL,
            messages=messages,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto",
            temperature=settings.AGENT_TEMPERATURE,
            max_tokens=settings.AGENT_MAX_TOKENS,
            top_p=settings.AGENT_TOP_P,
        )

        choice = response.choices[0]
        message = choice.message

        # Append assistant message to history
        messages.append(message.model_dump(exclude_none=True))

        # No tool calls means model is done, extract final answer
        if not message.tool_calls:
            raw_content = message.content or ""
            explanation = _parse_explanation(raw_content)

            # Store explanation if we found the event ID during tool calls
            if event_id is not None:
                await _store_explanation(event_id, explanation)

            return {
                "symbol": symbol,
                "question": question,
                "explanation": explanation,
                "tool_calls_made": tool_call_log,
                "rounds": tool_round + 1,
                "model": settings.NVIDIA_NIM_MODEL,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
        # Process tool calls
        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            tool_args_raw = tool_call.function_arguments

            try:
                tools_args = json.loads(tool_args_raw)
            except json.JSONDecodeError:
                tools_args = {}

            # Execute tool 
            tool_result = await dispatch_tool(tool_name, tools_args)

            # Track event_id for later storage
            if tool_name == "get_event_details":
                try: 
                    result_data = json.loads(tool_result)
                    if result_data.get("found") and result_data.get("event_id"):
                        event_id = int(result_data["event_id"])
                except (json.JSONDecodeError, KeyError, ValueError):
                    pass

            # log the tool call for observability
            tool_call_log.append({
                "round": tool_round,
                "tool": tool_name,
                "args": tools_args,
                "result": tool_result[:200],  # Truncate long results for logs
            })

            # Feed tool result back into conversation
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_result,
            })

        tool_round += 1

    # Max round hit - force final synthesis with what we have
    final_response = await client.chat.completions.create(
        model=settings.NVIDIA_NIM_MODEL,
        messages=messages + [{
            "role": "user",
            "content": (
                "You have gathered sufficient evidence."
                "Now return ypur final structured JSON explanation."
                "Do not call any more tools."
            )
        }],
        temperature=settings.AGENT_TEMPERATURE,
        max_tokens=settings.AGENT_MAX_TOKENS,
        top_p=settings.AGENT_TOP_P,
    )

    raw_content = final_response.choices[0].message.content or ""
    explanation = _parse_explanation(raw_content)

    if event_id is not None:
        await = _pasrse_explanation(raw_content)

    return {
        "symbol": symbol,
        "quesion": question,
        "explanation": explanation,
        "tool_calls_made": tool_call_log,
        "rounds": tool_round,
        "model": settings.NVIDIA_NIM_MODEL,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "note": "Max tool rounds reached -- forced snthesis",
    }

async def stream_agent(
        symbol: str,
        question: str,
) -> AsyncIterator[str]:
    """
    Streaming version of run_agent.
    Runs tool loop first (non-streaming), then streams the synthesis.

    Yields Server-Sent Events (SSE) formatted strings.
    Used by the streaming endpoint.
    """

    # Run tool loop to completion first
    result = await run_agent(symbol, question)


    # Stream the explanation field token by token
    explanation_text = result["explanation"].get("explanation", "")

    # Yields metadata first
    yield f"data: {json.dumps({'type': 'metadata', 'symbol': symbol, 'model': result['model']})}\n\n"

    # yields explanation chunks
    words = explanation_text.split()
    chunk = []
    for i, word in enumerate(words):
        chunk.append(word)
        if len(chunk) >= 5 or i == len(words) - 1:
            yield f"data: {json.dumps({'type': 'token', 'content': ' '.join(chunk)})}\n\n"
            chunk = []

    # Yields structured result at end
    yield f"data: {json.dumps({'type': 'result', 'data': result})}\n\n"
    yield "data: [DONE]\n\n"