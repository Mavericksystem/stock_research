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

    for item in payload.items:
        existing = await session.scalar(
            select(News.id).where(News.url == item.url)
        )