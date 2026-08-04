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