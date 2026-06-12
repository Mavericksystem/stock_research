import { useState, useEffect, useCallback } from "react";

const STOCKS = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "JPM", "V", "WMT"];
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

async function fetchEventsForSymbol(symbol) {
    try {
        const res = await fetch(`${API_BASE}/api/v1/stocks/${symbol}/events?limit=3`);
        if (!res.ok) return [];
        const json = await res.json();
        const raw = json?.data ?? [];
        return (Array.isArray(raw) ? raw : []).map((e) => ({ ...e, symbol }));
    } catch {
        return [];
    }
}

function SkeletonCard() {
    return (
        <div className="ec-card ec-card--skeleton" aria-hidden="true">
            <div className="ec-skeleton ec-skeleton--row">
                <div className="ec-skeleton--chip" />
                <div className="ec-skeleton--badge" />
            </div>
            <div className="ec-skeleton--date" />
        </div>
    );
}

function EventCard({ event, onClick }) {
    const isSpike = (event.event_type ?? "").includes("SPIKE");
    const mag = event.magnitude != null
        ? `${isSpike ? "+" : ""}${parseFloat(event.magnitude).toFixed(2)}%`
        : null;

    const zscore = event.normalized_score != null
        ? `z=${parseFloat(event.normalized_score).toFixed(1)}`
        : null;

    return (
        <button
            className="ec-card ec-card--interactive"
            onClick={onClick}
            title={`Why did ${event.symbol} ${isSpike ? "spike" : "drop"} on ${event.start_date}?`}
        >
            <div className="ec-card-row">
                <span className="ec-symbol">{event.symbol}</span>
                <span className={`ec-badge ${isSpike ? "ec-badge--spike" : "ec-badge--drop"}`}>
                    {isSpike ? "▲" : "▼"}{mag ? ` ${mag}` : ""}
                </span>
            </div>
            <div className="ec-card-meta">
                <span className="ec-date">{event.start_date}</span>
                {zscore && <span className="ec-zscore">{zscore}</span>}
            </div>
        </button>
    );
}

export default function EventsSidebar({ open, onToggle, onEventSelect }) {
    const [events, setEvents] = useState([]);
    const [loading, setLoading] = useState(true);
    const [lastRefresh, setLastRefresh] = useState(null);

    const loadEvents = useCallback(() => {
        setLoading(true);
        Promise.allSettled(STOCKS.map(fetchEventsForSymbol)).then((results) => {
            const all = results
                .filter((r) => r.status === "fulfilled")
                .flatMap((r) => r.value)
                .filter((e) => e?.start_date)
                .sort((a, b) => new Date(b.start_date) - new Date(a.start_date))
                .slice(0, 25);
            setEvents(all);
            setLoading(false);
            setLastRefresh(new Date());
        });
    }, []);

    useEffect(() => {
        loadEvents();
    }, [loadEvents]);

    const handleSelect = (event) => {
        const direction = (event.event_type ?? "").includes("SPIKE") ? "spike" : "drop";
        onEventSelect(`Why did ${event.symbol} ${direction} on ${event.start_date}?`);
    };

    return (
        <div className={`ec-root ${open ? "ec-root--open" : "ec-root--closed"}`}>
            <aside
                className="ec-sidebar"
                aria-label="Recent market anomalies"
            >
                <div className="ec-sidebar-header">
                    <span className="ec-sidebar-title">ANOMALIES</span>

                    <button
                        className="ec-refresh"
                        onClick={loadEvents}
                        disabled={loading}
                        aria-label="Refresh anomalies"
                        title="Refresh"
                    >
                        <svg
                            width="13"
                            height="13"
                            viewBox="0 0 13 13"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="1.5"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            className={loading ? "ec-spin" : ""}
                        >
                            <path d="M11.5 2A5.5 5.5 0 0 0 1 6.5" />
                            <path d="M1.5 11A5.5 5.5 0 0 0 12 6.5" />
                            <polyline points="11.5,2 11.5,5.5 8,5.5" />
                            <polyline points="1.5,11 1.5,7.5 5,7.5" />
                        </svg>
                    </button>
                </div>

                <div className="ec-sidebar-body">
                    {loading ? (
                        Array.from({ length: 6 }).map((_, i) => (
                            <SkeletonCard key={i} />
                        ))
                    ) : events.length === 0 ? (
                        <div className="ec-empty">
                            No anomalies in range
                        </div>
                    ) : (
                        events.map((event, i) => (
                            <EventCard
                                key={`${event.symbol}-${event.start_date}-${i}`}
                                event={event}
                                onClick={() => handleSelect(event)}
                            />
                        ))
                    )}
                </div>

                {lastRefresh && (
                    <div className="ec-footer">
                        Updated{" "}
                        {lastRefresh.toLocaleTimeString([], {
                            hour: "2-digit",
                            minute: "2-digit",
                        })}
                    </div>
                )}
            </aside>
        </div>
    );
}