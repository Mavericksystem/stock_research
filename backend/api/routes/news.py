from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
 
from backend.db.connection import get_db
from backend.db.models import News
from backend.api.schemas import RSSNewsRequest, APIResponse, NewsItemResponse
 
router = APIRouter()

@router.post("/rss", response_model=APIResponse)
async def ingest_rss_news(
    payload: RSSNewsRequest,
    session: AsyncSession = Depends(get_db),
):
    """Manual/external ingest path — kept as-is. The automated path is
    backend.ingestion.rss_poller, started as a background task."""
    inserted = 0
    skipped = 0
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
            source=item.source
            url=item.url,
            published_at=item.published_at,
            embedding=None,
            embedding_model=None,
            embedding_created_at=None,
        )
 
        session.add(news)
        inserted += 1

    await session.commit()
 
    return APIResponse(
        data={
            "inserted": inserted,
            "skipped": skipped,
        }
    )

@router.get("/latest", response_model=APIResponse)
async def get_latest_news(
    limit: int = Query(20, le=50),
    symbol: str | None = Query(None, description="Filter to one tracked ticker, e.g. AAPL"),
    session: AsyncSession = Depends(get_db),
):
    """Feeds the News panel in the right rail. Most recent first.
    RSS items are now ticker-scoped (rss_poller filters to the 10
    tracked symbols before insert), so `symbol` narrows to one stock;
    omit it to see the combined feed across all 10."""
    stmt = select(News).order_by(News.published_at.desc())

    if symbol:
        stmt = stmt.where(News.symbol == symbol.upper())

    stmt = stmt.limit(limit)
    result = await session.execute(stmt)
    items = result.scalars().all()