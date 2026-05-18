import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.engine import make_url
from sqlalchemy.orm import declarative_base

load_dotenv()

db_url = os.getenv("DATABASE_URL")

# Render/Heroku-style URLs often start with `postgres://`.
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# Normalize URL and translate sslmode (psycopg2-style) into asyncpg's `ssl`.
connect_args: dict[str, object] = {}
if db_url:
    url = make_url(db_url)

    # Force asyncpg driver for the async SQLAlchemy engine.
    if url.drivername == "postgresql":
        url = url.set(drivername="postgresql+asyncpg")

    # asyncpg does not accept `sslmode` kwarg; strip it from query.
    query = dict(url.query)
    sslmode = (query.pop("sslmode", None) or query.pop("ssl_mode", None))
    if sslmode:
        sslmode_normalized = str(sslmode).strip().lower()
        if sslmode_normalized not in {"disable", "allow"}:
            # `ssl=True` tells asyncpg to require SSL (Render Postgres typically needs this).
            connect_args["ssl"] = True

    url = url.set(query=query)
    db_url = str(url)

if not db_url:
    raise ValueError("DATABASE_URL is not set in .env file")

engine = create_async_engine(db_url, echo=False, connect_args=connect_args)

async_session_maker = async_sessionmaker(
    engine, expire_on_commit=False
)

Base = declarative_base()

async def get_db():
    async with async_session_maker() as session:
        yield session