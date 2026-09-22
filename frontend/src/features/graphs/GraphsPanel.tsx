import { useEffect, useMemo, useState } from "react";
import {
    Line,
    LineChart,
    ResponsiveContainer,
    YAxis,
} from "recharts";
import { getApiBaseUrl } from "../../lib/api-client";
import { TRACKED_STOCKS } from "../../lib/constants";

const GREEN = "#22c55e";
const RED = "#ef4444";

const STOCK_NAMES: Record<string, string> = {
    AAPL: "Apple",
    MSFT: "Microsoft",
    NVDA: "NVIDIA",
    GOOGL: "Google",
    AMZN: "Amazon",
    META: "Meta",
    TSLA: "Tesla",
    JPM: "JP Morgan",
    V: "Visa",
    WMT: "Walmart",
};

interface PricePoint {
    date: string;
    close: number;
}

interface LivePrice {
    price: number;
    t?: number;
}

interface StockData {
    symbol: string;
    history: PricePoint[];
    livePrice: number | null;
}

interface PriceResponse {
    data?: {
        prices?: Array<{
            date: string;
            close: number;
        }>;
    };
}

interface LiveSnapshot {
    prices?: Record<string, LivePrice>;
    connected?: boolean;
}

function Sparkline({
    data,
    color,
}: {
    data: PricePoint[];
    color: string;
}) {
    if (data.length < 2) {
        return <div className="h-[40px] w-full" />;
    }

    const values = data
        .map((point) => point.close)
        .filter(Number.isFinite);

    const min = Math.min(...values);
    const max = Math.max(...values);

    const range = max - min;

    const padding =
        range > 0
            ? range * 0.12
            : Math.max(Math.abs(min) * 0.001, 0.01);

    return (
        <ResponsiveContainer width="100%" height={40}>
            <LineChart
                data={data}
                margin={{
                    top: 5,
                    right: 1,
                    bottom: 5,
                    left: 1,
                }}
            >
                <YAxis
                    hide
                    domain={[
                        min - padding,
                        max + padding,
                    ]}
                />

                <Line
                    type="monotone"
                    dataKey="close"
                    stroke={color}
                    strokeWidth={1.7}
                    dot={false}
                    activeDot={false}
                    isAnimationActive={false}
                />
            </LineChart>
        </ResponsiveContainer>
    );
}

function StockRow({
    stock,
}: {
    stock: StockData;
}) {
    const sortedHistory = useMemo(() => {
        return [...stock.history].sort(
            (a, b) =>
                new Date(a.date).getTime() -
                new Date(b.date).getTime(),
        );
    }, [stock.history]);

    const lastHistoricalClose =
        sortedHistory[sortedHistory.length - 1]?.close ?? null;

    const previousClose =
        sortedHistory.length >= 2
            ? sortedHistory[sortedHistory.length - 2]?.close
            : null;

    const currentPrice =
        stock.livePrice ?? lastHistoricalClose;

    const referencePrice =
        stock.livePrice != null
            ? lastHistoricalClose
            : previousClose;

    const change =
        currentPrice != null &&
            referencePrice != null &&
            referencePrice !== 0
            ? ((currentPrice - referencePrice) / referencePrice) * 100
            : null;

    const isUp = change != null ? change >= 0 : true;
    const color = isUp ? GREEN : RED;

    const chartData =
        stock.livePrice != null
            ? [
                ...sortedHistory,
                {
                    date: "Live",
                    close: stock.livePrice,
                },
            ]
            : sortedHistory;

    return (
        <div className="flex min-h-[66px] items-center border-b border-[var(--border-soft)] px-1">
            <div className="min-w-0 flex-1">
                <div className="truncate font-mono text-[13px] font-semibold leading-[17px] text-[var(--text)]">
                    {stock.symbol}
                </div>

                <div className="truncate text-[11px] leading-[16px] text-[var(--text-dim)]">
                    {STOCK_NAMES[stock.symbol] ?? stock.symbol}
                </div>
            </div>

            <div className="mx-3 w-[78px] shrink-0">
                <Sparkline
                    data={chartData}
                    color={color}
                />
            </div>

            <div className="w-[91px] shrink-0 text-right">
                <div className="font-mono text-[13px] font-semibold leading-[17px] text-[var(--text)]">
                    {currentPrice != null
                        ? currentPrice.toLocaleString("en-US", {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2,
                        })
                        : "--"}
                </div>

                <div
                    className="mt-[1px] flex items-center justify-end gap-1 font-mono text-[11px] font-medium leading-[15px]"
                    style={{ color }}
                >
                    {change != null ? (
                        <>
                            <span>
                                {change >= 0 ? "+" : ""}
                                {change.toFixed(2)}%
                            </span>

                            <span
                                className="flex h-[14px] w-[14px] items-center justify-center rounded-full"
                                style={{
                                    backgroundColor: color,
                                }}
                            >
                                <svg
                                    width="9"
                                    height="9"
                                    viewBox="0 0 12 12"
                                    fill="none"
                                    xmlns="http://www.w3.org/2000/svg"
                                    className={
                                        isUp
                                            ? ""
                                            : "rotate-180"
                                    }
                                >
                                    <path
                                        d="M6 10V2M6 2L2.8 5.2M6 2L9.2 5.2"
                                        stroke="white"
                                        strokeWidth="1.7"
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                    />
                                </svg>
                            </span>
                        </>
                    ) : (
                        "--"
                    )}
                </div>
            </div>
        </div>
    );
}

function StockRowSkeleton() {
    return (
        <div className="flex min-h-[66px] items-center border-b border-[var(--border-soft)] px-1">
            <div className="min-w-0 flex-1">
                <div className="h-[14px] w-[54px] animate-pulse rounded bg-white/[0.06]" />

                <div className="mt-1.5 h-[11px] w-[64px] animate-pulse rounded bg-white/[0.04]" />
            </div>

            <div className="mx-3 h-[30px] w-[78px] animate-pulse rounded bg-white/[0.04]" />

            <div className="flex w-[91px] flex-col items-end">
                <div className="h-[14px] w-[64px] animate-pulse rounded bg-white/[0.06]" />

                <div className="mt-2 h-[11px] w-[42px] animate-pulse rounded bg-white/[0.04]" />
            </div>
        </div>
    );
}

export default function GraphsPanel() {
    const [stocks, setStocks] = useState<StockData[]>(
        TRACKED_STOCKS.map((symbol) => ({
            symbol,
            history: [],
            livePrice: null,
        })),
    );

    const [loading, setLoading] = useState(true);

    useEffect(() => {
        let cancelled = false;

        async function loadPrices() {
            setLoading(true);

            const results = await Promise.allSettled(
                TRACKED_STOCKS.map(async (symbol) => {
                    const response = await fetch(
                        `${getApiBaseUrl()}/api/v1/stocks/${symbol}/prices?limit=30`,
                    );

                    if (!response.ok) {
                        throw new Error(
                            `Failed to load ${symbol}: ${response.status}`,
                        );
                    }

                    const json =
                        (await response.json()) as PriceResponse;

                    const prices = Array.isArray(
                        json.data?.prices,
                    )
                        ? json.data.prices
                        : [];

                    return {
                        symbol,
                        history: prices
                            .filter(
                                (price) =>
                                    typeof price.close ===
                                    "number" &&
                                    Number.isFinite(
                                        price.close,
                                    ),
                            )
                            .map((price) => ({
                                date: price.date,
                                close: price.close,
                            })),
                        livePrice: null,
                    };
                }),
            );

            if (cancelled) {
                return;
            }

            setStocks(
                results.map((result, index) => {
                    if (result.status === "fulfilled") {
                        return result.value;
                    }

                    return {
                        symbol: TRACKED_STOCKS[index],
                        history: [],
                        livePrice: null,
                    };
                }),
            );

            setLoading(false);
        }

        loadPrices();

        return () => {
            cancelled = true;
        };
    }, []);

    useEffect(() => {
        const eventSource = new EventSource(
            `${getApiBaseUrl()}/api/v1/stocks/stream`,
        );

        eventSource.onmessage = (event) => {
            try {
                const snapshot =
                    JSON.parse(event.data) as LiveSnapshot;

                setStocks((current) =>
                    current.map((stock) => {
                        const live =
                            snapshot.prices?.[stock.symbol];

                        if (
                            !live ||
                            typeof live.price !== "number"
                        ) {
                            return stock;
                        }

                        return {
                            ...stock,
                            livePrice: live.price,
                        };
                    }),
                );
            } catch {
                // Ignore malformed SSE messages.
            }
        };

        eventSource.onerror = () => {
            // EventSource automatically attempts to reconnect.
        };

        return () => {
            eventSource.close();
        };
    }, []);

    return (
        <div className="flex h-full min-h-0 flex-col px-3">
            <div className="min-h-0 flex-1 overflow-y-auto overflow-x-hidden">
                <div className="flex h-[34px] items-end pb-1 font-sans text-[11px] font-medium text-[var(--text-dim)]">
                    Tracked Stocks
                </div>

                {loading
                    ? TRACKED_STOCKS.map((symbol) => (
                        <StockRowSkeleton key={symbol} />
                    ))
                    : stocks.map((stock) => (
                        <StockRow
                            key={stock.symbol}
                            stock={stock}
                        />
                    ))}
            </div>
        </div>
    );
}