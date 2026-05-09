import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from backend.db.models import News, EventNewsLink

# Fetch the most relevant news articles linked to a specific event,
# ordered by relevance score and publication time.

async def get_event_context(session: AsyncSession, event_id: int, limit: int = 5) -> list[dict[str, Any]]:
    stmt = (
        select(
            News.title,
            News.source,
            News.url,
            News.published_at,
            EventNewsLink.relevance_score,
        )
        .join(EventNewsLink, EventNewsLink.news_id == News.id)  # type: ignore[arg-type]
        .where(EventNewsLink.event_id == event_id)
        .order_by(desc(EventNewsLink.relevance_score), desc(News.published_at))
        .limit(limit)
    )
    res = await session.execute(stmt)
    rows = res.all()

    return [
        {
            "title": r.title,
            "source": r.source,
            "url": r.url,
            "published_at": r.published_at,
            "relevance_score": float(r.relevance_score) if r.relevance_score is not None else None,
        }
        for r in rows
    ]