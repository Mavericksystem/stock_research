"""
Orchestrator - mangaes the full agent reasoning loop.

Flow:
1. Receive symbol + question
2. Run tool-calling loop with Nvidia NIM
3. Dipatch each tool call to the actual DB fucntion
4. Synthesize structured explanation
5. Store explanation back to events table
6. Return structured result

No Strands dependency here intentionally - we impement the tool loop
directly against the OpenAI-compatible API. Strands wraps this patter 
but doing it manually shows deeper undwestanding and removes the framework as a single point of failure.

Streands MCP integration is additive on top of this - not a replacement.
"""

