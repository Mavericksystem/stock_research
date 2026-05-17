"""ASGI entrypoint shim.

This file exists so `uvicorn backend.main:app` works.
The actual FastAPI app is defined in `backend.api.main`.
"""

import logging
import sys

# Configure logging to capture tool errors and other debug info
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)

from backend.api.main import app
from fastapi.middleware.cors import CORSMiddleware

_cors_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://your-frontend.onrender.com",
    "https://stock-research-tibb.vercel.app",
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

__all__ = ["app"]
