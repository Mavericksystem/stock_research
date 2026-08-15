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

__all__ = ["app"]