import { getApiBaseUrl } from "../../lib/api-client";
import { NewsListResponseSchema } from "../../lib/schemas";

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

    const json: unknown = await res.json();
    const parsed = NewsListResponseSchema.safeParse(json);

    if (!parsed.success) {
        // eslint-disable-next-line no-console
        console.warn("News payload failed validation:", parsed.error.flatten());
        return [];
    }

    return (parsed.data.data ?? []).map((item) => ({
        id: item.id,
        symbol: item.symbol ?? "UNKNOWN",
        title: item.title ?? "Untitled",
        content: item.content,
        source: item.source,
        url: item.url,
        published_at: item.published_at,
    }));
}


function timeAgo(iso: string): string {
    const diffMs = Date.now() - new Date(iso).getTime();
    const mins = Math.floor(diffMs / 60000);
    if (mins < 1) return "just now";
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    return `${Math.floor(hours / 24)}d ago`;
}

export { timeAgo };
// complete