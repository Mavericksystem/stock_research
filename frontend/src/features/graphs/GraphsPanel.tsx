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