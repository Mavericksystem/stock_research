import asyncio
import sys
import os
from sqlalchemy import text

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.db.connection import engine, Base

# Ensure all models are registered in Base.metadata before create_all()
import backend.db.models as db_models

_REGISTERED_MODELS = db_models


RLS_TABLES = (
    "public.stocks",
    "public.prices",
    "public.technical_indicators",
    "public.events",
    "public.news",
    "public.event_news_link",
)


async def enable_rls(conn):
    print("Enabling Row Level Security (RLS) on public tables (deny-by-default)...")
    for table in RLS_TABLES:
        try:
            await conn.execute(text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY"))
        except Exception as exc:
            print(f"Failed to enable RLS on {table}: {exc}")
            raise
    print("RLS enabled successfully.")

async def init_models():
    print("Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await enable_rls(conn)
    print("Database tables created successfully.")


if __name__ == "__main__":
    asyncio.run(init_models())