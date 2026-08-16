import { useCallback, useEffect, useState } from "react";
import { motion } from "framer-motion";
import { fetchEventsForSymbol, type AnomalyEvent } from "./api";
import { TRACKED_STOCKS } from "../../lib/constants";

function SkeletonCard({ index }: { index: number }) {
    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: index * 0.04, duration: 0.2 }}
            aria-hidden="true"
            className="rounded-xl border border-[#3d3833] bg-[#2a2723] p-3"
        >
            <div className="mb-2 flex items-center justify-between">
                <div className="h-3 w-9 animate-pulse rounded bg-white/[0.06]" />
                <div className="h-[18px] w-12 animate-pulse rounded bg-white/[0.06]" />
            </div>
            <div className="h-2.5 w-[70px] animate-pulse rounded bg-white/[0.04]" />
        </motion.div>
    );
}

function EventCard({
    event,
    index,
    onClick,
}: {
    event: AnomalyEvent;
    index: number;
    onClick: () => void;
}) {
    const isSpike = (event.event_type ?? "").includes("SPIKE");
    const magnitude =
        event.magnitude != null
            ? `${isSpike ? "+" : ""}${parseFloat(String(event.magnitude)).toFixed(2)}%`
            : null;
    const zscore =
        event.normalized_score != null
            ? `z=${parseFloat(String(event.normalized_score)).toFixed(1)}`
            : null;

    return (
        <motion.button
            type="button"
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: Math.min(index * 0.025, 0.2), duration: 0.2 }}
            whileHover={{ x: 2, borderColor: "rgba(255,255,255,0.16)" }}
            whileTap={{ scale: 0.985 }}
            onClick={onClick}
            title={`Why did ${event.symbol} ${isSpike ? "spike" : "drop"} on ${event.start_date}?`}
            className="block w-full rounded-xl border border-[#3d3833] bg-[#2a2723] p-3 text-left transition-colors duration-200 hover:bg-[#322f2b] focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--amber)]/60"
        >
            <div className="mb-1 flex items-center justify-between gap-1.5">
                <span className="font-mono text-xs font-medium tracking-[0.02em] text-white">
                    {event.symbol}
                </span>
                <span className="flex shrink-0 items-center gap-1.5">
                    <span className="flex h-4 w-4 items-center justify-center">
                        <svg
                            viewBox="0 0 46 40"
                            xmlns="http://www.w3.org/2000/svg"
                            className={`h-3 w-3 ${isSpike ? "rotate-[270deg]" : "rotate-90"}`}
                            fill="currentColor"
                        >
                            <path d="M46 20.038c0-.7-.3-1.5-.8-2.1l-16-17c-1.1-1-3.2-1.4-4.4-.3-1.2 1.1-1.2 3.3 0 4.4l11.3 11.9H3c-1.7 0-3 1.3-3 3s1.3 3 3 3h33.1l-11.3 11.9c-1 1-1.2 3.3 0 4.4l16-17c.5-.5.8-1.1.8-1.9z" />
                        </svg>
                    </span>

                    <span className="font-mono text-[12px] font-medium tracking-[0.02em] text-white">
                        {magnitude}
                    </span>
                </span>
            </div>

            <div className="flex items-center justify-between gap-2 text-[12px] text-white/80">
                <span className="font-mono">{event.start_date}</span>
                {zscore && <span className="font-mono">{zscore}</span>}
            </div>
        </motion.button>
    );
}

export default function AnomaliesPanel({
    onEventSelect,
}: {
    onEventSelect: (question: string) => void;
}) {
    const [events, setEvents] = useState<AnomalyEvent[]>([]);
    const [loading, setLoading] = useState(true);
    const [lastRefresh, setLastRefresh] = useState<Date | null>(null);

    const loadEvents = useCallback(() => {
        setLoading(true);

        void Promise.allSettled(TRACKED_STOCKS.map(fetchEventsForSymbol)).then(
            (results) => {
                const all = results
                    .filter(
                        (result): result is PromiseFulfilledResult<AnomalyEvent[]> =>
                            result.status === "fulfilled",
                    )
                    .flatMap((result) => result.value)
                    .filter((event) => event?.start_date)
                    .sort(
                        (a, b) =>
                            new Date(b.start_date ?? 0).getTime() -
                            new Date(a.start_date ?? 0).getTime(),
                    )
                    .slice(0, 25);

                setEvents(all);
                setLoading(false);
                setLastRefresh(new Date());
            },
        );
    }, []);

    useEffect(() => {
        loadEvents();
    }, [loadEvents]);

    const handleSelect = (event: AnomalyEvent) => {
        const direction = (event.event_type ?? "").includes("SPIKE")
            ? "spike"
            : "drop";

        onEventSelect(`Why did ${event.symbol} ${direction} on ${event.start_date}?`);
    };

    return (
        <div className="flex h-full min-h-0 flex-col">
            <div className="flex shrink-0 items-center justify-between px-1 pb-2">
                <span className="font-mono text-[10px] uppercase tracking-[1px] text-[var(--text-dim)]">
                    Recent anomalies
                </span>

                <motion.button
                    type="button"
                    whileHover={{ scale: 1.08 }}
                    whileTap={{ scale: 0.92 }}
                    onClick={loadEvents}
                    disabled={loading}
                    aria-label="Refresh anomalies"
                    title="Refresh"
                    className="flex items-center rounded p-[3px] text-white/35 transition-colors hover:text-white/60 disabled:cursor-default disabled:opacity-50"
                >
                    <motion.svg
                        width="13"
                        height="13"
                        viewBox="0 0 13 13"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="1.5"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        animate={loading ? { rotate: 360 } : { rotate: 0 }}
                        transition={
                            loading
                                ? { duration: 0.8, repeat: Infinity, ease: "linear" }
                                : { duration: 0.15 }
                        }
                    >
                        <path d="M11.5 2A5.5 5.5 0 0 0 1 6.5" />
                        <path d="M1.5 11A5.5 5.5 0 0 0 12 6.5" />
                        <polyline points="11.5,2 11.5,5.5 8,5.5" />
                        <polyline points="1.5,11 1.5,7.5 5,7.5" />
                    </motion.svg>
                </motion.button>
            </div>

            <div className="h-0 min-h-0 flex-1 overflow-y-auto overflow-x-hidden overscroll-contain p-2 scrollbar-thin scrollbar-thumb-white/10 [touch-action:pan-y] [-webkit-overflow-scrolling:touch]">
                {loading ? (
                    <div className="space-y-2">
                        {Array.from({ length: 6 }).map((_, index) => (
                            <SkeletonCard key={index} index={index} />
                        ))}
                    </div>
                ) : events.length === 0 ? (
                    <div className="px-2.5 py-6 text-center font-mono text-[11px] text-white/25">
                        No anomalies in range
                    </div>
                ) : (
                    <div className="space-y-2">
                        {events.map((event, index) => (
                            <EventCard
                                key={`${event.symbol}-${event.start_date}-${index}`}
                                event={event}
                                index={index}
                                onClick={() => handleSelect(event)}
                            />
                        ))}
                    </div>
                )}
            </div>

            {lastRefresh && (
                <div className="shrink-0 border-t border-white/[0.04] px-1 pb-1 pt-2 font-mono text-[10px] text-white/25">
                    Updated{" "}
                    {lastRefresh.toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                    })}
                </div>
            )}
        </div>
    );
}