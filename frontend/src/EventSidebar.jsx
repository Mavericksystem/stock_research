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