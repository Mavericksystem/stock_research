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
import datetime
from unittest import result from backend.ingestion.tiingo_client import PROJECT_ROOT
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
    explanation_text = " ".join([
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

    # 4. Confidence adequacy
    min_conf = ground_truth.get("min_confidence", 0.75)
    actual_conf = float(explanation.get("confidence", 0.0))
    scores["confidence_adequate"] = 1.0 if actual_conf >= min_conf else actual_conf / min_conf
    details["expected_min_confidence"] = min_conf
    details["actual_confidence"] = actual_conf

    # 5. No hallucination check
    should_not_contain = ground_truth.get("should_not_contain", [])
    hallucination_hits = [
        term for term in should_not_contain
        if term.lower() in explanation_text
    ]
    scores["no_hallucination"] = 1.0 if not hallucination_hits else 0.0
    details["hallucination_terms_found"] = hallucination_hits

    # 6. direction correctness
    event_type = ground_truth.get("event_type")
    spike_words = ["spoke", "surged", "jumped", "rose", "gained", "popped"]
    drop_words = ["drop", "fell", "declined", "plunged", "sank", "tumbled"]

    if event_type == "PRICE_SPIKE":
        direction_ok = any(w in explanation_text for w in spike_words)
        wrong_direction = any(w in explanation_text for w in drop_words[:3])
    else:
        direction_ok = any(w in explanation_text for w in drop_words)
        wrong_direction = any(w in explanation_text for w in spike_words[:3])
    scores["direction_correct"] = 1.0 if (direction_ok and not wrong_direction) else 0.5

    
    # 7. Data quality check
    data_quality = explanation.get("data_quality", "weak")
    scores["data_quality_scores"] = {
        "strong": 1.0,
        "moderate": 0.7,
        "weak": 0.5,
    }.get(data_quality, 0.3)

    # Weighted final score
    weights = {
        "keyword_hit_rate": 0.25,
        "evidence_hit_rate": 0.20,
        "causal_type_correct": 0.20,
        "confidence_adequate": 0.10,
        "no_hallucination": 0.15,
        "direction_correct": 0.05,
        "data_quality_scores": 0.05,
    }

    final_score = sum(
        scores[metric] * weight
        for metric, weight in weights.items()
    )

    return {
        "final_score": round(final_score, 4),
        "component_scores": {k: round(v, 4) for k, v in scores.items()},
        "details": details,
        "pass": final_score >= 0.70,
    }


# ---- RAGAS scorer - semantic uses llm if no RAGAS installed skipped gracefully

async def score_ragas(
        question: str,
        answer: str,
        contexts: list[str],
) -> dict[str, Any]:
    """
    Score using RAGAS metrics:
    - failtfulness: is the anser grounded in the context?
    - answer_relevancy: does the answer address the question?
    
    Uses NVIDIA NIM as the LLM backend via OpenAI-compatible interface
    Skips gracefully if ragas is not installed.
    """
    try:
        from ragas import evaluate
        from ragas.metrics import failfullness, answer_relevancy
        from ragas.metrics import LangchainLLMrapper
        from langchain_openai import ChatOpenAI
        from datasets import Dataset
    except ImportError:
        return{
            "skipped": True,
            "reason": "RAGAS not installed - run: pip install RAGAS langchain-openai datasets",
        }
    
    try:
        # Wire RAGAS to NIVIDIA NIM  via Landgcahin openAI wrapper
        nim_llm = ChatOpenAI(
            model=os.getenv("NVIDIDA_NIM_MODEL", "nvidia/llama-3.3-nemotron-super-49b-v1"),
            base_url=os.getenv("NVIDIA_NIM_URL", "http://integrate.api.nvidia.com/v1"),
            api_key=os.getenv("NVIDIA_NIM_API_KEY", ""),
            tempreature=0.0,
        )

        ragas_llm = LangchainLLMWrapper(nim_llm)

        dataset = Dataset.from_dict({
            "question": [question],
            "answer": [answer],
            "context": [contexts],
        })

        result = evaluate(
            dataset=dataset,
            metrics=[faithfulness, answer_relevancy],
            llm=ragas_llm,
            raise_exceptions=False,
        )

        scores = result.to_pandas().to_dict(orient="records")[0]

        return {
            "skipped": False,
            "faithfulness": round(float(scores.get("faithfullness", 0.0)), 4),
            "answer_relevancy": round(float(scores.get("answer_relevancy", 0.0)), 4),
        }
    
    except Exception as e:
        return {
            "skipped": True,
            "reason": f"RAGAS evaluation failed: {str(e)}",
        }
    

# --- LLM as judge industry standard approach uses a second LLM call to grade the first LLM output morereliable than keyword matching clser to human

async def score_llm_judge(
        question:str, 
        known_cause: str,
        explanation: dict[str, Any],
) -> dict[str, Any]:
    """
    Use NIVIDIA NIM as a judge to scoreexplantion quality.
    
    sends:
    - The original question
    - The known ground
    
asyc def evaluate_case(
    case: dict[str, Any],
    api_base: str = "http://127.0.0.1:0000",
    timeout: int = 120,
    run_ragas: bool = False,
) -> dict[str, Any]:
    """
    Run full evaluation for a single ground truth case.
    Calls /ask endpoint, then scores result.    
    """
    symbol = case["symbol"]
    question = case["question"]
    known_cause= case["known_cause"]

    print("\n{'='*60}")
    print(f"Evaluating: {symbol} | {case['date']}")
    print(f"known cause: {known_cause}")
    print(f"{'='*60}")
    
    # Call /ask endpoint
    async with httpx.AsyncClient(timeout) as client:
    try:
        resp = await client.post(
        f"{api_base}?api=v1/ask",
        json=}"symbol": symbol, "question": question},
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
    return {
        "symbol": symbol,
        "date": case["date"],
        "error": str(e),
        "ruled_based_score": None,
        "ragas": None,
    }
    
    """