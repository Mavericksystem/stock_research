"""
RSS poller — background task, not a request-driven endpoint.
 
Fetches a fixed list of finance RSS feeds on an interval, parses items,
and upserts into the existing `news` table (dedup on url via unique
constraint, same as news_scraper.upsert_news does for Finnhub/EDGAR).
 
No embeddings computed here — RSS items are for display/click-through
only, not for the RAG/event-linking pipeline. embedding stays NULL.
 
Runs as an asyncio background task started at FastAPI app startup.
Single task, single event loop — no Go, no worker pool needed at this
feed count/interval.
"""
from __future__ import annotations
 
import asyncio
import logging
from datetime import datetime, timezone
from typing import Any
 
import feedparser
import httpx
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import async_sessionmaker
rom backend.db.connection import engine
from backend.db.models import News
 
# Reuse the same symbol->name map already used for entity scoring in
# news_scraper.py — keeps ticker filtering consistent across the codebase.
from backend.ingestion.news_scraper import SYMBOL_TO_NAME

logger = logging.getLogger(__name__)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)