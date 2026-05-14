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
