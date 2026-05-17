import os
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

load_dotenv()

def _normalize_db_url(raw_url: str | None) -> str | None:
    if not raw_url:
        return None

    db_url = raw_url.strip()

    # Ensure async SQLAlchemy driver scheme.
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    # Supabase expects SSL for external clients. Add it if missing.
    parts = urlsplit(db_url)
    if parts.hostname and "supabase.co" in parts.hostname:
        query = dict(parse_qsl(parts.query, keep_blank_values=True))
        if "sslmode" not in query and "ssl" not in query:
            query["sslmode"] = "require"
        db_url = urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))

    return db_url


# Prefer an explicit pooled connection URL in hosted environments.
db_url = _normalize_db_url(os.getenv("SUPABASE_POOLER_URL") or os.getenv("DATABASE_URL"))

if not db_url:
    raise ValueError("DATABASE_URL is not set in .env file")

engine = create_async_engine(db_url, echo=False)

async_session_maker = async_sessionmaker(
    engine, expire_on_commit=False
)

Base = declarative_base()

async def get_db():
    async with async_session_maker() as session:
        yield session