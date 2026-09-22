import { getApiBaseUrl } from "../../lib/api-client";
import { TRACKED_STOCKS } from "../../lib/constants";

export { TRACKED_STOCKS as STOCKS };

export interface AnomalyEvent {
  symbol: string;
  event_type?: string | null;
  magnitude?: number | string | null;
  normalized_score?: number | string | null;
  start_date?: string | null;
  [key: string]: unknown;
}

export async function fetchEventsForSymbol(
  symbol: string,
): Promise<AnomalyEvent[]> {
  try {
    const res = await fetch(
      `${getApiBaseUrl()}/api/v1/stocks/${symbol}/events?limit=3`,
    );

    if (!res.ok) return [];

    const json = (await res.json()) as { data?: unknown };
    const raw = json?.data ?? [];

    return (Array.isArray(raw) ? raw : []).map((event) => ({
      ...(event as Record<string, unknown>),
      symbol,
    }));
  } catch {
    return [];
  }
}
