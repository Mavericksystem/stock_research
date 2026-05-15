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