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