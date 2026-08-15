import { getApiBaseUrl } from "../../lib/api-client";

export interface PricePoint {
    date: string;
    close: number;
}

interface RawPriceRow {
    date: string;
    close: number;
    adj_close: number;
}

export async function fetchPriceHistory(
    symbol: string,
    limit = 30,
): Promise<PricePoint[]> {
    const res = await fetch(
        `${getApiBaseUrl()}/api/v1/stocks/${symbol}/prices?limit=${limit}`,
    );
    if (!res.ok) return [];

    const json = (await res.json()) as { data?: { prices?: RawPriceRow[] } };
    const rows = json?.data?.prices ?? [];

    return rows
        .map((r) => ({ date: r.date, close: r.adj_close ?? r.close }))
        .reverse();
}