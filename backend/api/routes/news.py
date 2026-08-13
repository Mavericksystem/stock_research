from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.connection import get_db
from backend.db.models import News
from backend.api.schemas import RSSNewsRequest, APIResponse

router = APIRouter()


@router.post("/rss", response_model=APIResponse)
async def ingest_rss_news(
    payload: RSSNewsRequest,
    session: AsyncSession = Depends(get_db),
):
    inserted = 0
    skipped = 0
    # Ingest each news item
    for item in payload.items:
        existing = await session.scalar(
            select(News.id).where(News.url == item.url)
        )

        if existing is not None:
            skipped += 1
            continue

        news = News(
            symbol=None,
            title=item.title,
            content=item.description,
            source=item.source,
            url=item.url,
            published_at=item.published_at,
            embedding=None,
            embedding_model=None,
            embedding_created_at=None,
        )

        session.add(news)
        inserted += 1

    await session.commit()