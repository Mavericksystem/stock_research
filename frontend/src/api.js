const BASE = import.meta.env.VITE_API_BASE_URL ?? "";

function extractSymbol(question) {
  if (!question) return null;

  const words = String(question).toUpperCase().match(/\b[A-Z]{1,10}\b/g) ?? [];
  const stop = new Set([
    "A",
    "AN",
    "THE",
    "WHY",
    "WHAT",
    "WHEN",
    "WHERE",
    "WHO",
    "HOW",
    "DID",
    "DO",
    "DOES",
    "IS",
    "ARE",
    "WAS",
    "WERE",
    "DROP",
    "DROPPED",
    "FALL",
    "FELL",
    "FALLING",
    "SPIKE",
    "SPIKED",
    "MOVE",
    "MOVED",
    "RECENT",
    "RECENTLY",
    "LAST",
    "TODAY",
    "YESTERDAY",
    "TOMORROW",
    "STOCK",
    "PRICE",
    "EXPLAIN",
  ]);

  const candidates = words.filter((w) => !stop.has(w) && w.length >= 2);
  return candidates.length > 0 ? candidates[candidates.length - 1] : null;
}

function safeJsonParse(value) {
  if (value == null) return null;
  if (typeof value === "object") return value;
  if (typeof value !== "string") return null;
  try {
    return JSON.parse(value);
  } catch {
    return null;
  }
}

function normalizeAskResponse(payload, fallbackSymbol) {
  const symbol = payload?.symbol ?? fallbackSymbol ?? null;
  const explanation = payload?.explanation ?? {};

  let answer = "";
  if (Array.isArray(explanation.explanation)) {
    answer = explanation.explanation.filter(Boolean).join("\n\n");
  } else if (typeof explanation.explanation === "string") {
    answer = explanation.explanation;
  } else if (typeof explanation.primary_cause === "string") {
    answer = explanation.primary_cause;
  } else {
    answer = "";
  }

  let sources = [];
  const toolCalls = payload?.tool_calls_made;
  if (Array.isArray(toolCalls)) {
    const newsCall = toolCalls.find((c) => c?.tool === "get_news_context");
    const parsed = safeJsonParse(newsCall?.result);
    if (parsed?.articles && Array.isArray(parsed.articles)) {
      sources = parsed.articles.map((a) => ({
        title: a.title ?? null,
        source: a.source ?? null,
        url: a.url ?? null,
        relevance_score: a.relevance_score ?? a.score ?? null,
      }));
    }
  }

  return {
    answer,
    symbol,
    event_type: payload?.event_type ?? null,
    event_date: payload?.event_date ?? null,
    magnitude: payload?.magnitude ?? null,
    sources,
  };
}

/**
 * POST /api/v1/ask
 * @param {string} question
 * @returns {Promise<{
 *   answer: string,
 *   symbol: string|null,
 *   event_type: string|null,
 *   event_date: string|null,
 *   magnitude: number|null,
 *   sources: Array<{title,source,url,relevance_score}>
 * }>}
 */
export async function askQuestion(question) {
  const symbol = extractSymbol(question) ?? "AAPL";

  const res = await fetch(`${BASE}/api/v1/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, symbol }),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text}`);
  }

  const json = await res.json();
  const payload = json?.data ?? json;
  return normalizeAskResponse(payload, symbol);
}
