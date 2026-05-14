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

#-----------------------------------------------------------------------------------
# Ground truth - what we know happend for each event
# These are facts verifiable from public earnings records and news

GROUND_TRUTH: list[dict[str, Any]] = [
    {
        "symbol": "v",
        "date": "2026-04-29",
        "question": "Why did V spike on 2026-04-29?",
        "event_type": "PRICE_SPIKE",
        "expected_magnitude_pct": 8.26,
        "expected_causal_type": "earnings",
        "expected_keywords": [
            "earnings", "revenue", "q2", "beat", "result",
        ],
        "expected_evidence_keywords": [
            "visa", "earnings", "popped", "market valur", "results",
        ],
        "should_not_contain": [
            "downgrade", "macro". "tariff",
        ],
        "known_cause": "visa Q2 2026 earnings beat - 17% revenue growth to $11.2B",
        "min_confidence": 0.80
    
    },
    {
        "symbol": "GOOGL",
        "date": 2026-04-30,
        "question": "Why did google stock spike on 2026-04-30?",
        "event_type": "PRICE_SPIKE",
        "expected_magnitude_pct": 9.96,
        "expected_causal_type": "earnings",
        "expected_keywords": [
            "cloud", "earnings", "revenue", "alphabet", "growth",
        ],
        "expected_evidence_keywords": [
            "alphabet", "google", "cloud", "surges", "financial results",
        ],
        "should_not_contain": [
            "downgrade", "macro",
        ],
        "should_not_contain": [
            "downgrade", "macro",
        ],
        "known_cause": "Alphabet Q1 2026 - Google cloud revenue gre 63% YoY",
        "min_confidence": 0.80
    },
]