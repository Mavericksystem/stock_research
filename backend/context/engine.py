from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from backend.db.models import News, EventNewsLink

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