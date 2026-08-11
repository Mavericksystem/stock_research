const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

export interface Source {
  title: string | null;
  source: string | null;
  url: string | null;
  relevance_score: number | null;
}

export interface AskResponse {
  answer: string;
  symbol: string | null;
  event_type: string | null;
  event_date: string | null;
  magnitude: number | null;
  sources: Source[];
}

export interface UserMessage {
  id: number;
  type: "user";
  content: string;
}

export interface AssistantMessage {
  id: number;
  type: "assistant";
  answer: string | null;
  symbol?: string | null;
  event_type?: string | null;
  event_date?: string | null;
  magnitude?: number | null;
  sources: Source[];
  error?: string;
}

export type Message = UserMessage | AssistantMessage;

export interface ToolStep {
  id: number;
  tool: string;
  label: string;
  status: "running" | "done";
}

export interface StreamHandlers {
  onToolCall?: (tool: string, status: "calling" | "done") => void;
  onToken?: (content: string) => void;
  onMetadata?: (symbol: string) => void;
  onResult?: (result: AskResponse) => void;
}

export function getApiBaseUrl(): string {
  return API_BASE;
}

export function extractSymbol(question: string): string | null {
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

  const candidates = words.filter(
    (word) => !stop.has(word) && word.length >= 2,
  );

  return candidates.length > 0
    ? candidates[candidates.length - 1]
    : null;
}

export function safeJsonParse(value: unknown): unknown {
  if (value == null) return null;
  if (typeof value === "object") return value;
  if (typeof value !== "string") return null;

  try {
    return JSON.parse(value) as unknown;
  } catch {
    return null;
  }
}

interface ExplanationPayload {
  explanation?: string | string[];
  primary_cause?: string;
}

interface ToolCallPayload {
  tool?: string;
  result?: unknown;
}

interface RawAskPayload {
  symbol?: string | null;
  explanation?: ExplanationPayload;
  event_type?: string | null;
  event_date?: string | null;
  magnitude?: number | null;
  tool_calls_made?: ToolCallPayload[];
}

export function normalizeAskResponse(
  payload: RawAskPayload | null | undefined,
  fallbackSymbol: string | null,
): AskResponse {
  const symbol = payload?.symbol ?? fallbackSymbol ?? null;
  const explanation = payload?.explanation ?? {};

  let answer = "";

  if (Array.isArray(explanation.explanation)) {
    answer = explanation.explanation.filter(Boolean).join("\n\n");
  } else if (typeof explanation.explanation === "string") {
    answer = explanation.explanation;
  } else if (typeof explanation.primary_cause === "string") {
    answer = explanation.primary_cause;
  }

  let sources: Source[] = [];
  const toolCalls = payload?.tool_calls_made;

  if (Array.isArray(toolCalls)) {
    const newsCall = toolCalls.find(
      (call) => call?.tool === "get_news_context",
    );
    const parsed = safeJsonParse(newsCall?.result) as
      | { articles?: unknown[] }
      | null;

    if (Array.isArray(parsed?.articles)) {
      sources = parsed.articles.map((article) => {
        const item = (article ?? {}) as Record<string, unknown>;
        const score = item.relevance_score ?? item.score;

        return {
          title: typeof item.title === "string" ? item.title : null,
          source: typeof item.source === "string" ? item.source : null,
          url: typeof item.url === "string" ? item.url : null,
          relevance_score:
            typeof score === "number" ? score : null,
        };
      });
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

export async function postJson(
  path: string,
  body: unknown,
): Promise<Response> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text}`);
  }

  return res;
}
