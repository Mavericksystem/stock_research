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
# Exposed for debugging (safe; does not include password)
DB_URL_NORMALIZED: str | None = None
DB_SSLMODE_EFFECTIVE: str | None = None
DB_SSL_CONFIG: dict[str, object] = {}
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
        DB_SSLMODE_EFFECTIVE = sslmode_normalized

        # asyncpg expects `ssl` (SSLContext/bool), not `sslmode`.
        # Match libpq semantics:
        # - require: encrypt, but do not verify cert chain
        # - verify-ca / verify-full: verify using CA bundle
        if sslmode_normalized in {"disable", "allow", "prefer"}:
            # Do not force SSL.
            connect_args.pop("ssl", None)
            DB_SSL_CONFIG = {"enabled": False, "mode": sslmode_normalized}
        elif sslmode_normalized == "require":
            import ssl as _ssl

            ssl_ctx = _ssl.SSLContext(_ssl.PROTOCOL_TLS_CLIENT)
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = _ssl.CERT_NONE
            connect_args["ssl"] = ssl_ctx
            DB_SSL_CONFIG = {
                "enabled": True,
                "mode": "require",
                "verify": False,
            }
        elif sslmode_normalized in {"verify-ca", "verify-full"}:
            try:
                import ssl as _ssl
                import certifi  # type: ignore

                ssl_ctx = _ssl.create_default_context(cafile=certifi.where())
                # For verify-ca, hostname check is not strictly required.
                # For verify-full, it is.
                ssl_ctx.check_hostname = sslmode_normalized == "verify-full"
                connect_args["ssl"] = ssl_ctx
                DB_SSL_CONFIG = {
                    "enabled": True,
                    "mode": sslmode_normalized,
                    "verify": True,
                    "check_hostname": ssl_ctx.check_hostname,
                    "cafile": certifi.where(),
                }
            except Exception as e:
                # If CA bundle isn't available, at least require encryption.
                connect_args["ssl"] = True
                DB_SSL_CONFIG = {
                    "enabled": True,
                    "mode": sslmode_normalized,
                    "verify": "unknown",
                    "fallback": True,
                    "error": str(e),
                }
        else:
            # Unknown value; safest default is to require encryption without verification.
            import ssl as _ssl

            ssl_ctx = _ssl.SSLContext(_ssl.PROTOCOL_TLS_CLIENT)
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = _ssl.CERT_NONE
            connect_args["ssl"] = ssl_ctx
            DB_SSL_CONFIG = {"enabled": True, "mode": sslmode_normalized, "verify": False}

    url = url.set(query=query)
    db_url = str(url)
    DB_URL_NORMALIZED = db_url

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