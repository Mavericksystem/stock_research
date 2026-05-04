import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.processing.signals import compute_signals
from backend.processing.events import detect_events
from scripts.fetch_prices import TARGET_SYMBOLS


async def main() -> None:
    print("Recomputing signals + events (10 symbols)")
    print(f"symbols={', '.join(TARGET_SYMBOLS)}")

    print("\n=== compute_signals ===")
    await asyncio.gather(*(compute_signals(sym) for sym in TARGET_SYMBOLS))

    print("\n=== detect_events ===")
    await asyncio.gather(*(detect_events(sym) for sym in TARGET_SYMBOLS))

    print("\nDONE")


if __name__ == "__main__":
    asyncio.run(main())
