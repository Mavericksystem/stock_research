import {
  extractSymbol,
  getApiBaseUrl,
  normalizeAskResponse,
  postJson,
} from "../../lib/api-client";
import type {
  AskResponse,
  StreamHandlers,
} from "../../lib/api-client";

export function getAnalysisApiBaseUrl(): string {
  return getApiBaseUrl();
}

export async function askQuestion(question: string): Promise<AskResponse> {
  const symbol = extractSymbol(question) ?? "AAPL";
  const res = await postJson("/api/v1/ask", { question, symbol });
  const json = (await res.json()) as { data?: unknown } & Record<string, unknown>;
  const payload = (json?.data ?? json) as Parameters<typeof normalizeAskResponse>[0];

  return normalizeAskResponse(payload, symbol);
}

export async function streamAskQuestion(
  question: string,
  handlers: StreamHandlers = {},
): Promise<void> {
  const symbol = extractSymbol(question) ?? "AAPL";

  const response = await fetch(
    `${getApiBaseUrl()}/api/v1/ask/stream`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, symbol }),
    },
  );

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

      let event: {
        type?: string;
        status?: "calling" | "done";
        tool?: string;
        content?: unknown;
        symbol?: string;
        data?: unknown;
      };

      try {
        event = JSON.parse(raw) as typeof event;
      } catch {
        continue;
      }

      if (event.type === "tool_call" && event.tool) {
        if (event.status === "calling") {
          handlers.onToolCall?.(event.tool, "calling");
        }
        if (event.status === "done") {
          handlers.onToolCall?.(event.tool, "done");
        }
      }

      if (event.type === "token" && typeof event.content === "string") {
        handlers.onToken?.(event.content);
      }

      if (event.type === "metadata" && event.symbol) {
        handlers.onMetadata?.(event.symbol);
      }

      if (event.type === "result" && event.data) {
        handlers.onResult?.(
          normalizeAskResponse(
            event.data as Parameters<typeof normalizeAskResponse>[0],
            symbol,
          ),
        );
      }
    }
  }
}
