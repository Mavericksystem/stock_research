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