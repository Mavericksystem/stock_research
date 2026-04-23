from fastapi import FastAPI
from backend.about.routes import stock, analysis

app = FastAPI(
    tittle = "Market Explanation Engine - Intelligence API",
)
