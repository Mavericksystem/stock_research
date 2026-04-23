from fastapi import FastAPI
from backend.about.routes import stock, analysis

app = FastAPI(
    tittle = "Market Explanation Engine - Intelligence API",
)

# API Versioning implemented per critique
API_V1 = "/api/v1"

app.include_router(stock.router, prefix=f"{API_V1}/stocks", tags=["Data & Signals"])
app.include_router(analysis.router, prefix=f"{API_V1}/analysis", tags=["Resoning Layer"])

@app.get("/health")
asynv def health_check():
    return{"status": "healthy". "version": "v1"}
