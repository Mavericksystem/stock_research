"""Evaluator — scores explanation quality against known ground truth events.

Two scoring layers:
1. Custom rule-based scoring — fast, no LLM cost, deterministic
2. RAGAS semantic scoring — faithfulness + answer relevancy (uses NVIDIA NIM)

Run this script directly:
    python backend/agents/evaluator.py

Output:
    - Per-event scores printed to console
    - Full JSON report saved to eval_report.json
    - Summary table printed at end

Ground truth cases are hardcoded — these are events where we know
exactly what happened from public record.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any

import httpx

# Ensure project root importable when run directly
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ---------------------------------------------------------------------------
# Ground Truth — what we KNOW happened for each event
# These are facts verifiable from public earnings records and news
# ---------------------------------------------------------------------------

GROUND_TRUTH: list[dict[str, Any]] = [
    {
        "symbol": "V",
        "date": "2026-04-29",
        "question": "Why did Visa spike on 2026-04-29?",
        "event_type": "PRICE_SPIKE",
        "expected_magnitude_pct": 8.26,
        "expected_causal_type": "earnings",
        "expected_keywords": [
            "earnings",
            "revenue",
            "q2",
            "beat",
            "results",
        ],
        "expected_evidence_keywords": [
            "visa",
            "earnings",
            "popped",
            "market value",
            "results",
        ],
        "should_not_contain": [
            "downgrade",
            "macro",
            "tariff",
        ],
        "known_cause": "Visa Q2 2026 earnings beat — 17% revenue growth to $11.2B",
        "min_confidence": 0.80,
    },
    {
        "symbol": "GOOGL",
        "date": "2026-04-30",
        "question": "Why did Google stock spike on 2026-04-30?",
        "event_type": "PRICE_SPIKE",
        "expected_magnitude_pct": 9.96,
        "expected_causal_type": "earnings",
        "expected_keywords": [
            "cloud",
            "earnings",
            "revenue",
            "alphabet",
            "growth",
        ],
        "expected_evidence_keywords": [
            "alphabet",
            "google",
            "cloud",
            "surges",
            "financial results",
        ],
        "should_not_contain": [
            "downgrade",
            "macro",
        ],
        "known_cause": "Alphabet Q1 2026 — Google Cloud revenue grew 63% YoY",
        "min_confidence": 0.80,
    },
    {
        "symbol": "META",
        "date": "2026-04-30",
        "question": "Why did Meta stock drop on 2026-04-30?",
        "event_type": "PRICE_DROP",
        "expected_magnitude_pct": -8.55,
        "expected_causal_type": "analyst_action",  # or earnings — both acceptable
        "expected_keywords": [
            "jpmorgan",
            "downgrade",
            "capex",
            "ai",
            "spending",
        ],
        "expected_evidence_keywords": [
            "meta",
            "dropped",
            "price target",
            "jpmorgan",
            "earnings",
        ],
        "should_not_contain": [
            "spike",
            "surged",
        ],
        "known_cause": "JPMorgan downgrade + AI CapEx concerns despite Q1 earnings beat",
        "min_confidence": 0.75,
        # META is harder — accept analyst_action OR earnings as valid
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
            "musk",
            "tweet",
            "chip",
            "rally",
            "popped",
        ],
        "expected_evidence_keywords": [
            "tesla",
            "popped",
            "stock",
            "best days",
        ],
        "should_not_contain": [
            "earnings beat",
            "revenue growth",
        ],
        "known_cause": "Elon Musk social media posts on chip advances + broader market rally",
        "min_confidence": 0.70,
        # TSLA is weakest evidence — accept lower confidence
        "acceptable_causal_types": ["product_announcement", "macro", "unknown"],
    },
]


# ---------------------------------------------------------------------------
# Rule-based scorer — deterministic, no LLM cost
# ---------------------------------------------------------------------------


def score_rule_based(
    ground_truth: dict[str, Any],
    explanation: dict[str, Any],
) -> dict[str, Any]:
    """Score explanation against ground truth using deterministic rules.

    Metrics:
    - keyword_hit_rate: % of expected keywords found in explanation text
    - evidence_hit_rate: % of expected evidence keywords found in evidence titles
    - causal_type_correct: 1.0 if causal_type matches, 0.0 if not
    - confidence_adequate: 1.0 if confidence >= min required, else scaled
    - no_hallucination: 1.0 if should_not_contain terms absent, 0.0 if present
    - direction_correct: 1.0 if explanation doesn't confuse spike/drop

    Final score: weighted average of above metrics.
    """

    scores: dict[str, float] = {}
    details: dict[str, Any] = {}

    explanation_field = explanation.get("explanation", "")
    if isinstance(explanation_field, list):
        explanation_body = " ".join(map(str, explanation_field))
    else:
        explanation_body = str(explanation_field)

    # Combine all explanation text for keyword search
    explanation_text = (
        " ".join(
            [
                str(explanation.get("primary_cause", "")),
                explanation_body,
                str(explanation.get("technical_context", "")),
                str(explanation.get("price_context", "")),
                str(explanation.get("caveats", "")),
            ]
        )
    ).lower()

    evidence = explanation.get("evidence", [])
    if isinstance(evidence, list):
        evidence_titles = " ".join(map(str, evidence)).lower()
    else:
        evidence_titles = str(evidence).lower()

    # 1. Keyword hit rate
    expected_kw = ground_truth.get("expected_keywords", [])
    if expected_kw:
        hits = [kw for kw in expected_kw if kw.lower() in explanation_text]
        scores["keyword_hit_rate"] = len(hits) / len(expected_kw)
        details["keyword_hits"] = hits
        details["keyword_misses"] = [
            kw for kw in expected_kw if kw.lower() not in explanation_text
        ]
    else:
        scores["keyword_hit_rate"] = 1.0

    # 2. Evidence keyword hit rate
    expected_ev = ground_truth.get("expected_evidence_keywords", [])
    if expected_ev:
        ev_hits = [kw for kw in expected_ev if kw.lower() in evidence_titles]
        scores["evidence_hit_rate"] = len(ev_hits) / len(expected_ev)
        details["evidence_hits"] = ev_hits
        details["evidence_misses"] = [
            kw for kw in expected_ev if kw.lower() not in evidence_titles
        ]
    else:
        scores["evidence_hit_rate"] = 1.0

    # 3. Causal type correctness
    expected_type = ground_truth.get("expected_causal_type", "")
    acceptable_types = ground_truth.get("acceptable_causal_types", [expected_type])
    actual_type = explanation.get("causal_type", "")
    scores["causal_type_correct"] = 1.0 if actual_type in acceptable_types else 0.0
    details["expected_causal_type"] = expected_type
    details["actual_causal_type"] = actual_type

    # 4. Confidence adequacy
    min_conf = float(ground_truth.get("min_confidence", 0.75))
    actual_conf = float(explanation.get("confidence", 0.0) or 0.0)
    scores["confidence_adequate"] = (
        1.0 if actual_conf >= min_conf else (actual_conf / min_conf if min_conf else 0.0)
    )
    details["expected_min_confidence"] = min_conf
    details["actual_confidence"] = actual_conf

    # 5. No hallucination check
    should_not = ground_truth.get("should_not_contain", [])
    hallucination_hits = [term for term in should_not if term.lower() in explanation_text]
    scores["no_hallucination"] = 1.0 if not hallucination_hits else 0.0
    details["hallucination_terms_found"] = hallucination_hits

    # 6. Direction correctness
    event_type = ground_truth.get("event_type", "")
    spike_words = ["spike", "surged", "jumped", "rose", "gained", "popped"]
    drop_words = ["drop", "fell", "declined", "plunged", "sank", "tumbled"]

    if event_type == "PRICE_SPIKE":
        direction_ok = any(w in explanation_text for w in spike_words)
        wrong_direction = any(w in explanation_text for w in drop_words[:3])
    else:
        direction_ok = any(w in explanation_text for w in drop_words)
        wrong_direction = any(w in explanation_text for w in spike_words[:3])

    scores["direction_correct"] = 1.0 if (direction_ok and not wrong_direction) else 0.5

    # 7. Data quality check
    data_quality = str(explanation.get("data_quality", "weak"))
    scores["data_quality_score"] = {
        "strong": 1.0,
        "moderate": 0.7,
        "weak": 0.3,
    }.get(data_quality, 0.3)

    # Weighted final score
    weights = {
        "keyword_hit_rate": 0.25,
        "evidence_hit_rate": 0.20,
        "causal_type_correct": 0.20,
        "confidence_adequate": 0.10,
        "no_hallucination": 0.15,
        "direction_correct": 0.05,
        "data_quality_score": 0.05,
    }

    final_score = sum(scores[metric] * weight for metric, weight in weights.items())

    return {
        "final_score": round(final_score, 4),
        "component_scores": {k: round(v, 4) for k, v in scores.items()},
        "details": details,
        "pass": final_score >= 0.70,
    }


# ---------------------------------------------------------------------------
# RAGAS scorer — semantic, uses LLM
# Optional — skipped gracefully if ragas not installed
# ---------------------------------------------------------------------------


async def score_ragas(
    question: str,
    answer: str,
    contexts: list[str],
) -> dict[str, Any]:
    """Score using RAGAS metrics.

    Metrics:
    - faithfulness: is the answer grounded in the contexts?
    - answer_relevancy: does the answer address the question?

    Uses NVIDIA NIM as the LLM backend via OpenAI-compatible interface.
    Skips gracefully if ragas is not installed.
    """

    try:
        from datasets import Dataset
        from langchain_openai import ChatOpenAI
        from ragas import evaluate
        from ragas.llms import LangchainLLMWrapper
        from ragas.metrics.collections import answer_relevancy, faithfulness
    except ImportError:
        return {
            "skipped": True,
            "reason": "ragas not installed — run: pip install ragas langchain-openai datasets",
        }

    try:
        # Wire NVIDIA NIM to LangChain OpenAI via environment variables
        os.environ["OPENAI_API_KEY"] = os.getenv("NVIDIA_NIM_API_KEY", "")
        os.environ["OPENAI_API_BASE"] = os.getenv("NVIDIA_NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
        nim_llm = ChatOpenAI(
            model=os.getenv(
                "NVIDIA_NIM_MODEL", "nvidia/llama-3.3-nemotron-super-49b-v1"
            ),
            temperature=0.0,
        )
        ragas_llm = LangchainLLMWrapper(nim_llm)

        dataset = Dataset.from_dict(
            {
                "question": [question],
                "answer": [answer],
                "contexts": [contexts],
            }
        )

        result = evaluate(
            dataset=dataset,
            metrics=[faithfulness, answer_relevancy],
            llm=ragas_llm,
            raise_exceptions=False,
        )

        scores = result.to_pandas().to_dict(orient="records")[0]
        return {
            "skipped": False,
            "faithfulness": round(float(scores.get("faithfulness", 0.0)), 4),
            "answer_relevancy": round(float(scores.get("answer_relevancy", 0.0)), 4),
        }
    except Exception as e:
        return {
            "skipped": True,
            "reason": f"RAGAS evaluation failed: {str(e)}",
        }


# ---------------------------------------------------------------------------
# LLM-as-judge — optional
# Uses a second LLM call to grade the first LLM's output.
# This is not wired into the CLI by default (keeps eval cheap).
# ---------------------------------------------------------------------------


async def score_llm_judge(
    question: str,
    known_cause: str,
    explanation: dict[str, Any],
) -> dict[str, Any]:
    """Use NVIDIA NIM as a judge to score explanation quality.

    Returns a dict with fields like: skipped, score_0_to_1, rationale.
    """

    api_key = os.getenv("NVIDIA_NIM_API_KEY", "")
    base_url = os.getenv("NVIDIA_NIM_BASE_URL", "https://integrate.api.nvidia.com/v1").rstrip(
        "/"
    )
    model = os.getenv("NVIDIA_NIM_MODEL", "nvidia/llama-3.3-nemotron-super-49b-v1")

    if not api_key:
        return {"skipped": True, "reason": "NVIDIA_NIM_API_KEY not set"}

    explanation_text = explanation.get("explanation", "")
    if isinstance(explanation_text, list):
        explanation_text = " ".join(map(str, explanation_text))
    else:
        explanation_text = str(explanation_text)

    judge_prompt = (
        "You are an expert evaluator of market-move explanations. "
        "Given a user question, a known ground-truth cause, and a model explanation, "
        "score how well the explanation matches the ground truth. "
        "Return ONLY valid JSON with keys: score_0_to_1 (number), pass (boolean), rationale (string)."
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": judge_prompt},
            {
                "role": "user",
                "content": (
                    f"Question: {question}\n\n"
                    f"Known cause: {known_cause}\n\n"
                    f"Explanation: {explanation_text}\n"
                ),
            },
        ],
        "temperature": 0.0,
        "max_tokens": 300,
    }

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{base_url}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            return {
                "skipped": False,
                "score_0_to_1": float(parsed.get("score_0_to_1", 0.0)),
                "pass": bool(parsed.get("pass", False)),
                "rationale": str(parsed.get("rationale", "")),
            }
    except Exception as e:
        return {"skipped": True, "reason": f"LLM judge failed: {str(e)}"}


async def evaluate_case(
    case: dict[str, Any],
    api_base: str = "http://127.0.0.1:8000",
    timeout: int = 120,
    run_ragas: bool = False,
) -> dict[str, Any]:
    """Run full evaluation for a single ground truth case.

    Calls `/api/v1/ask`, then scores result.
    """

    symbol = case["symbol"]
    question = case["question"]
    known_cause = case["known_cause"]

    print(f"\n{'='*60}")
    print(f"Evaluating: {symbol} | {case['date']}")
    print(f"Known cause: {known_cause}")
    print(f"{'='*60}")

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            resp = await client.post(
                f"{api_base}/api/v1/ask",
                json={"symbol": symbol, "question": question},
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            return {
                "symbol": symbol,
                "date": case["date"],
                "error": str(e),
                "rule_based": None,
                "ragas": None,
            }

    explanation = data.get("data", {}).get("explanation", {})
    tool_calls = data.get("data", {}).get("tool_calls_made", [])
    rounds = data.get("data", {}).get("rounds", 0)

    rule_scores = score_rule_based(case, explanation)

    print(f"Primary cause: {explanation.get('primary_cause', 'N/A')}")
    print(f"Causal type:   {explanation.get('causal_type', 'N/A')}")
    print(f"Confidence:    {explanation.get('confidence', 'N/A')}")
    print(f"Data quality:  {explanation.get('data_quality', 'N/A')}")
    print(f"Tool rounds:   {rounds}")
    print(
        f"\nRule-based score: {rule_scores['final_score']} | Pass: {rule_scores['pass']}"
    )
    print(f"  keyword_hit_rate:   {rule_scores['component_scores']['keyword_hit_rate']}")
    print(f"  evidence_hit_rate:  {rule_scores['component_scores']['evidence_hit_rate']}")
    print(f"  causal_type:        {rule_scores['component_scores']['causal_type_correct']}")
    print(f"  no_hallucination:   {rule_scores['component_scores']['no_hallucination']}")

    result: dict[str, Any] = {
        "symbol": symbol,
        "date": case["date"],
        "known_cause": known_cause,
        "explanation": explanation,
        "tool_calls": len(tool_calls) if isinstance(tool_calls, list) else 0,
        "rounds": rounds,
        "rule_based": rule_scores,
        "ragas": None,
    }

    if run_ragas:
        print("Running RAGAS scoring...")
        explanation_text = explanation.get("explanation", "")
        if isinstance(explanation_text, list):
            explanation_text = " ".join(map(str, explanation_text))

        contexts = explanation.get("evidence", [])
        if not isinstance(contexts, list):
            contexts = [str(contexts)]

        ragas_scores = await score_ragas(
            question=question,
            answer=str(explanation_text),
            contexts=[str(c) for c in contexts],
        )
        result["ragas"] = ragas_scores

        if not ragas_scores.get("skipped"):
            print(f"RAGAS faithfulness:      {ragas_scores.get('faithfulness')}")
            print(f"RAGAS answer_relevancy:  {ragas_scores.get('answer_relevancy')}")

    return result


async def run_evaluation(
    run_ragas: bool = False,
    api_base: str = "http://127.0.0.1:8000",
    output_file: str = "eval_report.json",
) -> None:
    """Run full evaluation across all ground truth cases."""

    print("\nMARKET EXPLANATION ENGINE — EVALUATION REPORT")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"Cases: {len(GROUND_TRUTH)}")
    print(f"RAGAS enabled: {run_ragas}")

    results: list[dict[str, Any]] = []
    for case in GROUND_TRUTH:
        result = await evaluate_case(
            case=case,
            api_base=api_base,
            run_ragas=run_ragas,
        )
        results.append(result)

    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(
        f"{'Symbol':<8} {'Date':<12} {'Score':<8} {'Pass':<6} {'Causal Type':<22} {'Confidence'}"
    )
    print(f"{'-'*8} {'-'*12} {'-'*8} {'-'*6} {'-'*22} {'-'*10}")

    total_score = 0.0
    passed = 0

    for r in results:
        if r.get("error"):
            print(f"{r['symbol']:<8} {r['date']:<12} ERROR: {r['error']}")
            continue

        rb = r.get("rule_based") or {}
        score = float(rb.get("final_score", 0.0) or 0.0)
        passed_flag = "✅" if rb.get("pass") else "❌"
        causal = r.get("explanation", {}).get("causal_type", "N/A")
        conf = r.get("explanation", {}).get("confidence", "N/A")

        total_score += score
        if rb.get("pass"):
            passed += 1

        print(f"{r['symbol']:<8} {r['date']:<12} {score:<8.4f} {passed_flag:<6} {causal:<22} {conf}")

    valid_results = [r for r in results if not r.get("error")]
    avg_score = (total_score / len(valid_results)) if valid_results else 0.0
    pass_rate = (100 * passed // len(valid_results)) if valid_results else 0

    if valid_results:
        print(f"\nAverage score: {avg_score:.4f}")
        print(f"Pass rate:     {passed}/{len(valid_results)} ({pass_rate}%)")

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_cases": len(GROUND_TRUTH),
        "passed": passed,
        "average_score": round(avg_score, 4),
        "ragas_enabled": run_ragas,
        "results": results,
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    print(f"\nFull report saved to: {output_file}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate Market Explanation Engine")
    parser.add_argument(
        "--ragas",
        action="store_true",
        help="Enable RAGAS semantic scoring (uses NVIDIA NIM credits)",
    )
    parser.add_argument(
        "--api",
        default="http://127.0.0.1:8000",
        help="API base URL (default: http://127.0.0.1:8000)",
    )
    parser.add_argument(
        "--output",
        default="eval_report.json",
        help="Output file for full report (default: eval_report.json)",
    )
    args = parser.parse_args()

    asyncio.run(
        run_evaluation(
            run_ragas=args.ragas,
            api_base=args.api,
            output_file=args.output,
        )
    )