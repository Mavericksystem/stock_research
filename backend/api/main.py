from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import stock, analysis, ask

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
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# API Versioning implemented per critique
API_V1 = "/api/v1"

app.include_router(stock.router, prefix=f"{API_V1}/stocks", tags=["Data & Signals"])
app.include_router(analysis.router, prefix=f"{API_V1}/analysis", tags=["Reasoning Layer"])
app.include_router(ask.router, prefix=f"{API_V1}/ask", tags=["Intelligence"])

@app.get("/")
async def root():
    return {
        "name": "Market Explanation Engine - Intelligence API",
        "status": "ok",
        "docs": "/docs",
        "health": "/health",
        "api_v1": API_V1,
    }

@app.get("/health")
async def health_check():
    return{"status": "healthy", "version": "v1"}
