import { getApiBaseUrl } from "../../lib/api-client";
import { TRACKED_STOCKS } from "../../lib/constants";

export { TRACKED_STOCKS as STOCKS };

export async function fetchEventsForSymbol(symbol) {
  try {
    const res = await fetch(`${getApiBaseUrl()}/api/v1/stocks/${symbol}/events?limit=3`);
    if (!res.ok) return [];

    const json = await res.json();
    const raw = json?.data ?? [];
    return (Array.isArray(raw) ? raw : []).map((event) => ({ ...event, symbol }));
  } catch {
    return [];
  }
}