from fastapi import FastAPI
from backend.api.routes import stock, analysis

app = FastAPI(
    title="Market Explanation Engine - Intelligence API",
)

# API Versioning implemented per critique
API_V1 = "/api/v1"

app.include_router(stock.router, prefix=f"{API_V1}/stocks", tags=["Data & Signals"])
app.include_router(analysis.router, prefix=f"{API_V1}/analysis", tags=["Reasoning Layer"])


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
