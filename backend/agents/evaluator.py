""" 
Evaluator = scores explantion quality against known ground truth events.

Two scoring layers:
1. Custom rule-based scoring - fast, no LLM cost, deterministic
2. RAGAS semantic scoring - faithfulness * answer relevancy (uses NIVIDIDA NIM)

Output: 
     - Per-event scores printed to console
     - Full JSON report saved to eval_report.json
     - Summary table printed at end

Ground truth casws are hardcoded - these are evetns where we know 
exactly what happend from from public record.

"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import datetime from backend.ingestion.tiingo_client import PROJECT_ROOT
import datetime, timezone
from typing import Any

import httpx

# Ensure project root importable when run directly
project_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

    