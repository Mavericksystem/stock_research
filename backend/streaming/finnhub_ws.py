from __future__ import annotations
 
import asyncio
import json
import logging
from typing import Any
import websockets
from websockets.exceptions import ConnectionClosed
 
from backend.config.settings import settings

from backend.ingestion.news_scraper import SYMBOL_TO_NAME
 
TRACKED_SYMBOLS = list(SYMBOL_TO_NAME.keys())
 
logger = logging.getLogger(__name__)

FINNHUB_WS_URL = "wss://ws.finnhub.io"
 
# Shared state — read by the SSE endpoint, written only by this module's
# listener loop. Plain dict assignment is atomic under asyncio's single
# event loop, no lock needed.
latest_prices: dict[str, dict[str, Any]] = {}
 
# Exposed so the SSE endpoint / a health check can report connection state
# without reaching into listener internals.
connection_state: dict[str, Any] = {"connected": False, "last_tick_at": None}

_MAX_BACKOFF_SECONDS = 30
 
 
async def _subscribe_all(ws: Any) -> None:
    for symbol in TRACKED_SYMBOLS:
        await ws.send(json.dumps({"type": "subscribe", "symbol": symbol}))

        async def _handle_message(raw: str) -> None:
    try:
        msg = json.loads(raw)
    except json.JSONDecodeError:
        return

    if msg.get("type") != "trade":
        return  # Finnhub also sends "ping"/other control messages — ignore

    for trade in msg.get("data", []):
        symbol = trade.get("s")
        price = trade.get("p")

        ts = trade.get("t")
        if not symbol or price is None:
            continue

        latest_prices[symbol] = {"price": price, "t": ts}
        connection_state["last_tick_at"] = ts

async def run_price_feed_loop() -> None:
    """Long-running loop — call once via asyncio.create_task at startup."""
    if not settings.FINNHUB_API_KEY:
        logger.warning("[price_feed] FINNHUB_API_KEY not set — live graphs disabled")
        return

    backoff = 1
    url = f"{FINNHUB_WS_URL}?token={settings.FINNHUB_API_KEY}"

    while True:
        try:
            async with websockets.connect(url, ping_interval=20, ping_timeout=10) as ws:
                logger.info("[price_feed] connected, subscribing to %d symbols", len(TRACKED_SYMBOLS))