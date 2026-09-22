import { getApiBaseUrl } from "../../lib/api-client";
import { LiveSnapshotSchema, PriceResponseSchema } from "../../lib/schemas";

export interface PricePoint {
    date: string;
    close: number;
}

export async function fetchPriceHistory(
    symbol: string,
    limit = 30,
): Promise<PricePoint[]> {
    const res = await fetch(
        `${getApiBaseUrl()}/api/v1/stocks/${symbol}/prices?limit=${limit}`,
    );
    if (!res.ok) return [];

    const json: unknown = await res.json();
    const parsed = PriceResponseSchema.safeParse(json);

    if (!parsed.success) {
        // eslint-disable-next-line no-console
        console.warn(
            "Price history payload failed validation:",
            parsed.error.flatten(),
        );
        return [];
    }

    const rows = parsed.data.data?.prices ?? [];

    return rows
        .map((r) => ({ date: r.date, close: r.adj_close ?? r.close }))
        .reverse();
}

export interface LiveTick {
    price: number;
    t: number;
}

export interface LiveSnapshot {
    prices: Record<string, LiveTick>;
    connected: boolean;
}

export function subscribeLivePrices(
    onSnapshot: (snapshot: LiveSnapshot) => void,
): () => void {
    const es = new EventSource(`${getApiBaseUrl()}/api/v1/stocks/stream`);

    es.onmessage = (event) => {
        let raw: unknown;

        try {
            raw = JSON.parse(event.data);
        } catch {
            // malformed JSON — skip this tick, next one will arrive in ~1s
            return;
        }

        const parsed = LiveSnapshotSchema.safeParse(raw);
        if (!parsed.success) {
            // eslint-disable-next-line no-console
            console.warn(
                "Live price snapshot failed validation:",
                parsed.error.flatten(),
            );
            return;
        }

        onSnapshot({
            prices: (parsed.data.prices ?? {}) as Record<string, LiveTick>,
            connected: parsed.data.connected ?? false,
        });
    };

    es.onerror = () => {
        /* no-op — EventSource handles reconnection itself */
    };

    return () => es.close();
}