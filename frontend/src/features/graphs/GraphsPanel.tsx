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