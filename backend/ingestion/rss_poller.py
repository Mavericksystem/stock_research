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