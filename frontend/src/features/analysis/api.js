import { extractSymbol, normalizeAskResponse, postJson, getApiBaseUrl } from "../../lib/api-client";

export function getAnalysisApiBaseUrl() {
  return getApiBaseUrl();
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

  const res = await postJson("/api/v1/ask", { question, symbol });
  const json = await res.json();
  const payload = json?.data ?? json;
  return normalizeAskResponse(payload, symbol);
}

export async function streamAskQuestion(question, handlers = {}) {
  const symbol = extractSymbol(question) ?? "AAPL";
  const response = await fetch(`${getApiBaseUrl()}/api/v1/ask/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, symbol }),
  });

  if (!response.ok || !response.body) {
    throw new Error("Streaming request failed");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const raw = line.slice(6).trim();
      if (!raw) continue;
      if (raw === "[DONE]") return;

      let event;
      try {
        event = JSON.parse(raw);
      } catch {
        continue;
      }

      if (event.type === "tool_call") {
        if (event.status === "calling") handlers.onToolCall?.(event.tool, "calling");
        if (event.status === "done") handlers.onToolCall?.(event.tool, "done");
      }

      if (event.type === "token" && typeof event.content === "string") {
        handlers.onToken?.(event.content);
      }

      if (event.type === "metadata" && event.symbol) {
        handlers.onMetadata?.(event.symbol);
      }

      if (event.type === "result" && event.data) {
        handlers.onResult?.(normalizeAskResponse(event.data, symbol));
      }
    }
  }
}