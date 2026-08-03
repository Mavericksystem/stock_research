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