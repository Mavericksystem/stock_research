import { getApiBaseUrl } from "../../lib/api-client";

export interface NewsItem {
    id: number;
    symbol: string;
    title: string;
    content: string | null;
    source: string;
    url: string;
    published_at: string;
}

export async function fetchLatestNews(
    limit = 20,
    symbol?: string,
): Promise<NewsItem[]> {
    const params = new URLSearchParams({ limit: String(limit) });
    if (symbol) params.set("symbol", symbol);

    const res = await fetch(
        `${getApiBaseUrl()}/api/v1/news/latest?${params.toString()}`,
    );

    if (!res.ok) return [];

    const json = (await res.json()) as { data?: unknown };
    const raw = json?.data ?? [];