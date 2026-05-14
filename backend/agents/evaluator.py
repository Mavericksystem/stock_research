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
    {
        "symbol": "META",
        "date": "2026-04-30",
        "question": "Why did META stock drop on 2026-04-30?",
        "event_type": "PRICE_DROP",
        "expected_magnitude_pct": -8.55,
        "expected_causal_type": "analyst_action",
        "expected_keywords": [
            "jpmorgan", "downgrade", "capex", "ai", "spending",
        ],
        "expected_evidence_keywords": [
            "meta", "jpmorgan", "droppend", "price target", "earnings",
        ],
        "should_not_contain": [
            "spike", "surged",
        ],
        "known_cause": "JPMorgan downgrade + AI capex concers depite Q1 earnings beat",
        "min_confidence": 0.75,
        "acceptable_causal_types": ["analyst_action", "earnings", "macro"],
    },
    {
        "symbol": "TSLA",
        "date": "2026-04-15",
        "question": "Why did Tesla stock spike on 2026-04-15?",
        "event_type": "PRICE_SPIKE",
        "expected_magnitude_pct": 7.62,
        "expected_causal_type": "product_announcement",
        "expected_keywords": [
            "musk", "tesla", "chip", "rally", "popped",
        ],
        "expected_evidence_keywords": [
            "tesla", "popped", "stock", "besy days",
        ],
        "should_not_contain": [
            "earnings beat", "revenue growth",
        ],
        "known_cause": "Elon Musk social media posts on chip advances + broader market rally",
        "min_confidence": 0.70,
        "acceptable_causal_types": ["product_announcement", "macro", "unknown"],
    },
]



#---- Rule based scorer = deteministic no LLM cost

def score_rule_based(
      ground_truth: dict[str, Any],
      explanation: dict[str, Any],
) -> dict[str, Any]:
    """
    
    Score explanation against ground truth using deterministic rules,
    
    
    Metrics:
    - Keyword_hit_rate: % of expected keywords found in explanation text
    - evidence_hit_rate: % of expected evidence keywords found in evidence titles
    - causal_type_correct: 1.0 if causal_type matches, 0.0 of not 
    - comfidence_adequate: 1.0 if comfidence >= min required, 0.0 if not
    - no_hallucination: 1.0 if should_not_contain terms absent, 0.0 if present
    - directon_correct: 1.0 of explanation desn't confuse spike/drop

    Final score: weighted average of above metrics
    
    """ 
    scores: dict[str, float] = {} 
    details: dict[str, Any] = {}

    # Combine all explanation text for keyword search
    explanation.text = " ".join([
        explanation.get("primary_cause", ""),
        explanation.get("explanation", "") if isinstance(explanation.get("explanation"), str)
        else " ".join(explanation.get("explanation", [])),
        explanation.get("technical_context", ""),
        explanation.get("price_context", ""),
        explanation.get("caveats", ""),
    ]).lower()

    evidence_titles = " ".join(explanation.get("evidence", [])).lower()

    # 1. Keyword hit rate
    expected_kw = ground_truth.get("expected_keywords", [])
    if expected_kw:
        hits = [kw for kw in expected_kw if kw.lower() in explanation_text]
        scores["keyword_hit_rate"] = len(hits) / len(expected_kw)
        details["keyword_hits"] = hits
        details["keyword_misses"] = [kw for kw in expected_kw if kw.lower() not in explanation_text]
    else:
        scores["keyword_hit_rate"] = 1.0

    # 2. Evidence keyword hit rate
    expected_ev = ground_truth.get("expected_evidence_keywords", [])
    if expected_ev:
        ev_hits = [kw for kw in expected_ev if kw.lower() in evidence_titles]
        scores["evidence_hit_rate"] = len(ev_hits) / len(expected_ev)
        details["evidence_hits"] = ev_hits
        details["evidence_misses"] = [kw for kw in expected_ev if kw.lower() not in evidence_titles]
    else:
        scores["evidence_hit_rate"] = 1.0

    # 3. Causal type correctness 
    expected_type = ground_truth.get("expected_causal_type")
    acceptable_types = ground_truth.get(
        "acceptable_causal_types", [expected_type]
    )
    actual_type = explanation.get("causal_type", "")
    scores["causal_type_correct"] = 1.0 if actual_type in acceptable_types else 0.0
    details["expected_causal_type"] = expected_type
    details["actual_causal_type"] = actual_type