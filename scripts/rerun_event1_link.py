import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import delete

from backend.db.connection import async_session_maker
from backend.db.models import EventNewsLink
from backend.ingestion.news_scraper import link_event_to_news


async def main() -> None:
    async with async_session_maker() as session:
        await session.execute(delete(EventNewsLink).where(EventNewsLink.event_id == 1))
        await session.commit()

    n = await link_event_to_news(event_id=1, symbol="AAPL")
    print(f"relinked rows={n}")


if __name__ == "__main__":
    asyncio.run(main())
