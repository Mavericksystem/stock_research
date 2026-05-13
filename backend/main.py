"""ASGI entrypoint shim.

This file exists so `uvicorn backend.main:app` works.
The actual FastAPI app is defined in `backend.api.main`.
"""

from backend.api.main import app

__all__ = ["app"]
