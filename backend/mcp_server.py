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
 