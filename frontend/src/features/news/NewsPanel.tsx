import { useCallback, useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { fetchLatestNews, timeAgo, type NewsItem } from "./api";

function NewsCardSkeleton({ index }: { index: number }) {
    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: index * 0.03, duration: 0.2 }}
            className="h-[112px] rounded-xl border border-[#3d3833] bg-[#2a2723] p-3"
        >
            <div className="mb-3 h-3 w-20 animate-pulse rounded bg-white/[0.06]" />
            <div className="mb-2 h-3 w-full animate-pulse rounded bg-white/[0.06]" />
            <div className="h-3 w-3/4 animate-pulse rounded bg-white/[0.04]" />
        </motion.div>
    );
}

function NewsCard({ item, index }: { item: NewsItem; index: number }) {
    return (
        <motion.a
            href={item.url}
            target="_blank"
            rel="noopener noreferrer"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{
                delay: Math.min(index * 0.025, 0.2),
                duration: 0.3,
            }}
            whileHover={{
                y: -18,
                scale: 1.015,
                zIndex: 50,
                transition: {
                    type: "spring",
                    stiffness: 420,
                    damping: 26,
                },
            }}
            className="group relative block h-[112px] overflow-hidden rounded-xl border border-[#3d3833] bg-[#2a2723] p-3 no-underline shadow-[0_4px_12px_rgba(0,0,0,0.15)] transition-colors duration-200 hover:border-[var(--amber-border)] hover:bg-[#322f2b] hover:shadow-[0_16px_30px_rgba(0,0,0,0.28)]"
        >
            {/* Top heading */}
            <div className="mb-2 flex items-center justify-between">
                <span className="font-mono text-[9px] font-semibold tracking-[0.14em] text-[var(--text-dim)]">
                    NEWS
                </span>

                <span className="rounded bg-[var(--amber-dim)] px-1.5 py-0.5 font-mono text-[10px] font-medium text-[var(--amber)]">
                    {item.symbol}
                </span>
            </div>

            {/* Compact title */}
            <div className="line-clamp-2 text-[12px] font-medium leading-[1.35] text-[var(--text)] transition-opacity duration-200 group-hover:opacity-0">
                {item.title}
            </div>

            {/* Expanded content */}
            <div className="pointer-events-none absolute inset-0 flex flex-col justify-between rounded-xl bg-[#2a2723] p-3 opacity-0 transition-opacity duration-150 group-hover:opacity-100">
                <div>
                    <div className="mb-2 flex items-center justify-between">
                        <span className="font-mono text-[9px] font-semibold tracking-[0.14em] text-[var(--amber)]">
                            NEWS
                        </span>

                        <span className="rounded bg-[var(--amber-dim)] px-1.5 py-0.5 font-mono text-[10px] font-medium text-[var(--amber)]">
                            {item.symbol}
                        </span>
                    </div>

                    <div className="text-[12px] font-medium leading-[1.4] text-[var(--text)]">
                        {item.title}
                    </div>
                </div>