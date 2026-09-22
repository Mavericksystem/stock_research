import { AskResponseSchema, RawAskPayloadSchema } from "./schemas";

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

  // .at(-1) returns T | undefined regardless of noUncheckedIndexedAccess,
  // so this stays correctly typed as string | null either way.
  return candidates.at(-1) ?? null;
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

/**
 * Normalizes a raw /api/v1/ask (or streamed "result" event) payload into
 * the shape the UI renders.
 *
 * Runtime-validated at both ends:
 *   1. RawAskPayloadSchema checks the incoming payload before we touch it —
 *      an unknown/malformed backend shape falls back to `{}` instead of
 *      propagating garbage into the rest of the function.
 *   2. AskResponseSchema checks what we're about to hand to the UI — this
 *      is what actually prevents e.g. a non-numeric `magnitude` reaching
 *      `EventBadge`'s `.toFixed(2)` call in DashboardPage.tsx.
 */
export function normalizeAskResponse(
  rawPayload: unknown,
  fallbackSymbol: string | null,
): AskResponse {
  const parsedPayload = RawAskPayloadSchema.safeParse(rawPayload);

  if (!parsedPayload.success) {
    // eslint-disable-next-line no-console
    console.warn(
      "Ask response payload failed validation, using defaults:",
      parsedPayload.error.flatten(),
    );
  }

  const payload = parsedPayload.success ? parsedPayload.data : {};

  const symbol = payload.symbol ?? fallbackSymbol ?? null;
  const explanation = payload.explanation ?? {};

  let answer = "";

  if (Array.isArray(explanation.explanation)) {
    answer = explanation.explanation.filter(Boolean).join("\n\n");
  } else if (typeof explanation.explanation === "string") {
    answer = explanation.explanation;
  } else if (typeof explanation.primary_cause === "string") {
    answer = explanation.primary_cause;
  }

  let sources: Source[] = [];
  const toolCalls = payload.tool_calls_made;

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

  const result = {
    answer,
    symbol,
    event_type: payload.event_type ?? null,
    event_date: payload.event_date ?? null,
    magnitude: payload.magnitude ?? null,
    sources,
  };

  const validated = AskResponseSchema.safeParse(result);

  if (validated.success) {
    return validated.data;
  }

  // eslint-disable-next-line no-console
  console.error(
    "Normalized ask response failed final validation, falling back:",
    validated.error.flatten(),
  );

  return {
    answer: result.answer || "Something went wrong reading this response.",
    symbol,
    event_type: null,
    event_date: null,
    magnitude: null,
    sources: [],
  };
}

export async function postJson(
  path: string,
  body: unknown,
  signal?: AbortSignal,
): Promise<Response> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text}`);
  }

  return res;
}
