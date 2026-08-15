from __future__ import annotations
 
import asyncio
import json
import logging
from typing import Any
import websockets
from websockets.exceptions import ConnectionClosed
 
from backend.config.settings import settings