import asyncio
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import stock, analysis, ask, news

logger = logging.getLogger(__name__)
 
_price_feed_task: asyncio.Task | None = None

app = FastAPI(
    title="Market Explanation Engine - Intelligence API",
)

# CORS: allow the local Vite dev server (and optional Render frontend).
# This must live on the actual app module so CORS works regardless of entrypoint.
_cors_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://stockmarketmind.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Security headers: this API only ever serves JSON, never HTML, so the
# policy is intentionally locked down to "nothing should execute" rather
# than trying to allowlist frontend script/style sources (that CSP belongs
# on the frontend's own responses, e.g. via frontend/vercel.json).
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = (
        "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


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

# NOTE: the unauthenticated /api/v1/debug/db_test diagnostic endpoint that
# used to live here (returning DB host, port, DNS resolution, and SSL config
# to any caller) was removed as part of the pre-launch security pass — see
# stock_project/checklist in Obsidian for details. If DB connectivity needs
# to be checked again, do it via a local script against backend.db.connection
# rather than a public route.

@app.on_event("startup")
async def start_background_tasks():
    global _price_feed_task
    from backend.streaming.finnhub_ws import run_price_feed_loop

    _price_feed_task = asyncio.create_task(run_price_feed_loop())
    logger.info("Price feed background task started (RSS runs via GH Actions cron, not in-process)")

@app.on_event("shutdown")
async def stop_background_tasks():
    if _price_feed_task:
        _price_feed_task.cancel()

        try:
            await _price_feed_task
        except asyncio.CancelledError:
            pass