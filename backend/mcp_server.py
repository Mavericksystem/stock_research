"""
MCP Server — Market Explanation Engine
 
Exposes agent tools as MCP protocol endpoints.
Compatible with Claude Desktop, Strands SDK, and any MCP client.
 
Transport: stdio (standard for local MCP servers)
 
"""
 
from __future__ import annotations
 
import asyncio
import json
import os
import sys
from typing import Any
 
# Ensure project root importable when run directly
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
 
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    CallToolResult,
)
 
from backend.agents.tools import (
    get_event_details,
    get_technical_state,
    get_news_context,
    get_price_history,
)
from backend.agents.orchestrator import run_agent
 


# ----- MCP Server instance
 
server = Server("market-explanation-engine")


# ----- Tool registry — maps MCP tool names to handler functions

 
@server.list_tools()
async def list_tools() -> list[Tool]:
    """Declare all tools available to MCP clients."""
    return [
        Tool(
            name="get_event_details",
            description=(
                "Get details about a statistically significant price event for a stock. "
                "Returns event type (PRICE_SPIKE or PRICE_DROP), magnitude percentage, "
                "z-score anomaly score, RSI at event time, volatility, and trend context. "
                "Use this first when investigating any stock price movement."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock ticker symbol e.g. AAPL, MSFT, NVDA, V, GOOGL",
                    },
                    "date_str": {
                        "type": "string",
                        "description": "Optional date in YYYY-MM-DD format to target a specific event",
                    },
                },
                "required": ["symbol"],
            },
        ),
        Tool(
            name="get_technical_state",
            description=(
                "Get technical indicator state for a stock on a specific date. "
                "Returns RSI-14 with overbought/oversold interpretation, "
                "20-day and 50-day moving averages, daily return percentage, "
                "20-day volatility, and price vs SMA position. "
                "Use after get_event_details to characterize market conditions."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock ticker symbol",
                    },
                    "date_str": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format",
                    },
                },
                "required": ["symbol", "date_str"],
            },
        ),
        Tool(
            name="get_news_context",
            description=(
                "Get top ranked news articles causally linked to a specific price event. "
                "Articles are ranked by semantic similarity, temporal proximity, "
                "and entity relevance. Returns titles, sources, publication times, "
                "relevance scores, and content previews. "
                "Requires event_id from get_event_details. "
                "This is the primary causal evidence layer."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "event_id": {
                        "type": "integer",
                        "description": "Event ID from get_event_details response",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of articles to return (default 5, max 10)",
                        "default": 5,
                    },
                },
                "required": ["event_id"],
            },
        ),