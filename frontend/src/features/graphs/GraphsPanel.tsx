import { useEffect, useMemo, useState } from "react";
import {
    Line,
    LineChart,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts";
import {
    fetchPriceHistory,
    subscribeLivePrices,
    type PricePoint,
} from "../api";
import { TRACKED_STOCKS } from "../../../lib/constants";

const GREEN = "#22c55e";
const RED = "#ef4444";

function ChartSkeleton() {
    return (
        <div className="flex h-[180px] w-full items-center justify-center">
            <div className="h-[140px] w-full animate-pulse rounded-lg bg-white/[0.04]" />
        </div>
    );
}

export default function GraphsPanel() {
    const [symbol, setSymbol] = useState<string>(TRACKED_STOCKS[0]);
    const [history, setHistory] = useState<PricePoint[]>([]);
    const [loading, setLoading] = useState(true);
    const [livePrice, setLivePrice] = useState<number | null>(null);
    const [connected, setConnected] = useState(false);

    useEffect(() => {
        setLoading(true);
        setLivePrice(null);
        fetchPriceHistory(symbol, 30)
            .then(setHistory)
            .finally(() => setLoading(false));
    }, [symbol]);

    useEffect(() => {
        const cleanup = subscribeLivePrices((snapshot) => {
            setConnected(snapshot.connected);
            const tick = snapshot.prices[symbol];
            if (tick) setLivePrice(tick.price);
        });
        return cleanup;
    }, [symbol]);

    const chartData = useMemo(() => {
        if (history.length === 0) return [];
        const withLive =
            livePrice != null
                ? [...history, { date: "Live", close: livePrice }]
                : history;
        return withLive;
    }, [history, livePrice]);

    const firstClose = history[0]?.close;
    const lastClose = livePrice ?? history[history.length - 1]?.close;
    const isUp =
        firstClose != null && lastClose != null ? lastClose >= firstClose : true;
    const lineColor = isUp ? GREEN : RED;

    const pctChange =
        firstClose != null && lastClose != null && firstClose !== 0
            ? ((lastClose - firstClose) / firstClose) * 100
            : null;

    return (
        <div className="flex h-full flex-col gap-3 p-3">
            <div className="flex items-center justify-between gap-2">
                <select
                    value={symbol}
                    onChange={(e) => setSymbol(e.target.value)}
                    className="rounded-md border border-[var(--border)] bg-[var(--surface)] px-2 py-1 font-mono text-xs text-[var(--text)] outline-none"
                >
                    {TRACKED_STOCKS.map((sym) => (
                        <option key={sym} value={sym}>
                            {sym}
                        </option>
                    ))}
                </select>

                <div className="flex items-center gap-1.5 font-mono text-[10px] text-[var(--text-dim)]">
                    <span
                        className={`h-1.5 w-1.5 rounded-full ${connected ? "bg-[var(--green)]" : "bg-white/20"
                            }`}
                    />
                    {connected ? "LIVE" : "OFFLINE"}
                </div>
            </div>

            {lastClose != null && (
                <div className="flex items-baseline gap-2">
                    <span className="font-mono text-lg font-semibold text-[var(--text)]">
                        ${lastClose.toFixed(2)}
                    </span>
                    {pctChange != null && (
                        <span
                            className="font-mono text-xs font-medium"
                            style={{ color: lineColor }}
                        >
                            {pctChange >= 0 ? "+" : ""}
                            {pctChange.toFixed(2)}%
                        </span>
                    )}
                </div>
            )}