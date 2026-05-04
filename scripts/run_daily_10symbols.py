import asyncio
import os
import sys
from collections.abc import Awaitable, Callable

# Ensure project root is importable when running from /scripts
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.fetch_prices import TARGET_SYMBOLS, ingest_market_data
from backend.processing.signals import compute_signals
from backend.processing.events import detect_events
from backend.ingestion.news_scraper import run_context_for_symbol
from sqlalchemy import text

from backend.db.connection import async_session_maker


async def _run_step(step_name: str, coro: Callable[[], Awaitable[None]]) -> None:
    print(f"\n=== {step_name} ===")
    try:
        await coro()
    except Exception as e:
        print(f"[WARN] Step '{step_name}' failed: {e}")


async def _run_per_symbol(
    step_name: str,
    symbol: str,
    coro: Callable[[str], Awaitable[None]],
) -> None:
    try:
        await coro(symbol)
    except Exception as e:
        print(f"[WARN] {step_name} failed for {symbol}: {e}")


async def main() -> None:
    print("\nDAILY PIPELINE (10 symbols)")
    print(f"symbols={', '.join(TARGET_SYMBOLS)}")

    # 1) Prices
    await _run_step("Fetch prices (yfinance) -> prices table", ingest_market_data)

    # 2) Signals / indicators
    print("\n=== Compute signals -> technical_indicators table ===")
    await asyncio.gather(*( _run_per_symbol("compute_signals", sym, compute_signals) for sym in TARGET_SYMBOLS))

    # 3) Detect events
    print("\n=== Detect events -> events table ===")
    await asyncio.gather(*( _run_per_symbol("detect_events", sym, detect_events) for sym in TARGET_SYMBOLS))

    # 4) News + embeddings + linking
    print("\n=== Fetch news + embed + link -> news/event_news_link tables ===")

    async def _print_symbol_stats(symbol: str) -> None:
        async with async_session_maker() as session:
            q1 = text(
                """
                SELECT
                    COUNT(*) AS total,
                    COUNT(*) FILTER (WHERE embedding IS NOT NULL) AS embedded
                FROM news
                WHERE symbol = :symbol;
                """
            )
            q2 = text(
                """
                SELECT COUNT(*) AS links
                FROM event_news_link enl
                JOIN events e ON e.id = enl.event_id
                WHERE e.symbol = :symbol;
                """
            )
            n = (await session.execute(q1, {"symbol": symbol})).one()
            l = (await session.execute(q2, {"symbol": symbol})).one()
        print(f"[{symbol}] news={n.total} embedded={n.embedded} links={l.links}")

    for sym in TARGET_SYMBOLS:
        try:
            await run_context_for_symbol(sym, days_back=10)
        except Exception as e:
            print(f"[WARN] run_context_for_symbol failed for {sym}: {e}")
            continue

        try:
            await _print_symbol_stats(sym)
        except Exception as e:
            print(f"[WARN] stats query failed for {sym}: {e}")

    print("\nDONE")


if __name__ == "__main__":
    asyncio.run(main())
