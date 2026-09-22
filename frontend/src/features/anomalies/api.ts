import { getApiBaseUrl } from "../../lib/api-client";
import { TRACKED_STOCKS } from "../../lib/constants";
import { AnomalyEventsResponseSchema } from "../../lib/schemas";

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

    const json: unknown = await res.json();
    const parsed = AnomalyEventsResponseSchema.safeParse(json);

    if (!parsed.success) {
      // eslint-disable-next-line no-console
      console.warn(
        "Anomaly events payload failed validation:",
        parsed.error.flatten(),
      );
      return [];
    }

    const rows = parsed.data.data ?? [];

    return rows.map((event) => ({
      ...event,
      symbol,
    }));
  } catch {
    return [];
  }
}
