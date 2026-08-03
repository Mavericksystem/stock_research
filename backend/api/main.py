import asyncio
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import stock, analysis, ask, news

logger = logging.getLogger(__name__)
 
_rss_task: asyncio.Task | None = None

app = FastAPI(
    title="Market Explanation Engine - Intelligence API",
)

# CORS: allow the local Vite dev server (and optional Render frontend).
# This must live on the actual app module so CORS works regardless of entrypoint.
_cors_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://your-frontend.onrender.com",
]

if not any(m.cls is CORSMiddleware for m in app.user_middleware):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins,
        allow_origin_regex=r"^https://.*\.vercel\.app$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# API Versioning implemented per critique
API_V1 = "/api/v1"

app.include_router(stock.router, prefix=f"{API_V1}/stocks", tags=["Data & Signals"])
app.include_router(analysis.router, prefix=f"{API_V1}/analysis", tags=["Reasoning Layer"])
app.include_router(ask.router, prefix=f"{API_V1}/ask", tags=["Intelligence"])
app.include_router(news.router, prefix=f"{API_V1}/news", tags=["News"],)

@app.get("/")
async def root():
    return {
        "name": "Market Explanation Engine - Intelligence API",
        "status": "ok",
        "docs": "/docs",
        "health": "/health",
        "api_v1": API_V1,
    }

@app.api_route("/health", methods=["GET", "HEAD"])
async def health_check(request: Request):
    return {"status": "healthy", "version": "v1"}

@app.api_route("/api/health", methods=["GET", "HEAD"])
async def api_health_check(request: Request):
    return {"status": "healthy", "version": "v1"}

@app.get(f"{API_V1}/debug/db_test")
async def debug_db_test():
    """Run a lightweight DB connectivity test and return result or full traceback."""
    from sqlalchemy import text
    from backend.db.connection import engine
    import traceback
    import socket

    def _db_diagnostics() -> dict:
        try:
            url = engine.url
            safe_url = url.render_as_string(hide_password=True)
            host = url.host
            port = url.port
            query = dict(url.query)
            from backend.db import connection as _dbc
            ssl_info = {
                "sslmode_effective": getattr(_dbc, "DB_SSLMODE_EFFECTIVE", None),
                "ssl_config": getattr(_dbc, "DB_SSL_CONFIG", None),
                "normalized_url": getattr(_dbc, "DB_URL_NORMALIZED", None),
            }
        except Exception:
            return {"database_url": None, "host": None, "port": None, "query": None, "dns": None}

        dns = None
        if host:
            try:
                infos = socket.getaddrinfo(host, port or 5432, type=socket.SOCK_STREAM)
                # Keep this small; just enough to see IPv4 vs IPv6.
                dns = [
                    {"family": i[0], "socktype": i[1], "proto": i[2], "address": i[4][0]}
                    for i in infos
                ][:10]
            except Exception as e:
                dns = {"error": str(e)}

        return {
            "database_url": safe_url,
            "host": host,
            "port": port,
            "query": query,
            "dns": dns,
            "ssl": ssl_info,
        }

    try:
        async with engine.connect() as conn:
            res = await conn.execute(text("SELECT 1"))
            val = res.scalar()
        return {"status": "ok", "db_result": val, "db": _db_diagnostics()}
    except Exception as e:
        tb = traceback.format_exc()
        return {"status": "error", "error": str(e), "traceback": tb, "db": _db_diagnostics()}

@app.on_event("startup")
async def start_rss_poller():
    global _rss_task
    from backend.ingestion.rss_poller import run_rss_poll_loop

    _rss_task = asyncio.create_task(run_rss_poll_loop())
    logger.info("RSS poller background task started")

@app.on_event("shutdown")
async def stop_rss_poller():
    if _rss_task:
        _rss_task.cancel()