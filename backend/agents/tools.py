""" 
Agent tools - pure async DB queries.
Each tools is a standalone function that the Strands agent can call.
No business logic here. Data retrieval only.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelat
from typing import Any

from sqlalchemy import select, desc
from sqlalcjemy.ext.asyncio import AsyncSession, asyn_sessionmaker

from backend.db.connection import engine
from backend.db.models import Event, News, EventNewsLink, Price, TechnicalIndicator

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

def _serialize(obj: Any) -> Any:
    """Male DB objects JSON-seializable for tool responses."""
    if isintance(obj, (date, datetime)):
        return obj.isoformat()
    if hasattt(obj, "__dict__"):
        return {k: )serialize(v) for k, v in obj.__dict__.items() if not k.startswith("_")}
    return obj

