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

const CARD_COLORS = [
    {
        bg: "bg-[#000000]",
        text: "text-[#E1DCC9]",
        muted: "text-[#E1DCC9]/60",
        symbol: "text-[#E1DCC9]",
        symbolBorder: "border-[#E1DCC9]/30",
    },
    {
        bg: "bg-[#1F150C]",
        text: "text-[#E1DCC9]",
        muted: "text-[#E1DCC9]/60",
        symbol: "text-[#E1DCC9]",
        symbolBorder: "border-[#E1DCC9]/30",
    },
    {
        bg: "bg-[#412D15]",
        text: "text-[#E1DCC9]",
        muted: "text-[#E1DCC9]/60",
        symbol: "text-[#E1DCC9]",
        symbolBorder: "border-[#E1DCC9]/30",
    },
    {
        bg: "bg-[#B8B3A3]",
        text: "text-[#1F150C]",
        muted: "text-[#1F150C]/60",
        symbol: "text-[#1F150C]",
        symbolBorder: "border-[#1F150C]/30",
    },
];

function NewsCard({ item, index }: { item: NewsItem; index: number }) {
    const cardColor = CARD_COLORS[index % CARD_COLORS.length];

    return (
        <motion.a
            href={item.url}
            target="_blank"
            rel="noopener noreferrer"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{
                delay: Math.min(index * 0.025, 0.2),
                duration: 0.35,
            }}
            whileHover={{
                y: -28,
                scale: 1.02,
                zIndex: 100,
                transition: {
                    type: "spring",
                    stiffness: 420,
                    damping: 28,
                },
            }}
            className={`group relative -mt-8 first:mt-0 block min-h-[142px] overflow-hidden rounded-2xl border border-white/10 ${cardColor.bg} p-4 no-underline shadow-[0_8px_18px_rgba(0,0,0,0.22)]`}
        >
            <div className="mb-3 flex items-center justify-between">
                <span
                    className={`rounded-md border ${cardColor.symbolBorder} bg-transparent px-2 py-1 font-mono text-[10px] font-semibold ${cardColor.symbol}`}
                >
                    {item.symbol}
                </span>
            </div>

            <div
                className={`line-clamp-2 text-[13px] font-medium leading-[1.45] ${cardColor.text}`}
            >
                {item.title}
            </div>

            <div
                className={`absolute bottom-4 left-4 right-4 flex items-center justify-between gap-3 font-mono text-[9px] ${cardColor.muted}`}
            >
                <span className="truncate">{item.source}</span>
                <span className="shrink-0">{timeAgo(item.published_at)}</span>
            </div>

            <div
                className={`pointer-events-none absolute inset-0 flex flex-col justify-between rounded-2xl ${cardColor.bg} p-4 opacity-0 transition-opacity duration-150 group-hover:opacity-100`}
            >
                <div>
                    <div className="mb-3 flex items-center justify-between">
                        <span
                            className={`rounded-md border ${cardColor.symbolBorder} bg-transparent px-2 py-1 font-mono text-[10px] font-semibold ${cardColor.symbol}`}
                        >
                            {item.symbol}
                        </span>
                    </div>

                    <p
                        className={`m-0 text-[13px] font-medium leading-[1.45] ${cardColor.text}`}
                    >
                        {item.title}
                    </p>
                </div>

                <div className="flex items-center justify-between gap-3">
                    <span
                        className={`truncate font-mono text-[9px] ${cardColor.muted}`}
                    >
                        {item.source} · {timeAgo(item.published_at)}
                    </span>

                    <span
                        className={`shrink-0 font-mono text-[9px] font-semibold tracking-[0.12em] ${cardColor.symbol}`}
                    >
                        READ MORE →
                    </span>
                </div>
            </div>
        </motion.a>
    );
}

export default function NewsPanel() {
    const [items, setItems] = useState<NewsItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(false);

    const load = useCallback(() => {
        setLoading(true);
        setError(false);

        fetchLatestNews(20)
            .then((data) => {
                setItems(data);
            })
            .catch(() => {
                setError(true);
            })
            .finally(() => {
                setLoading(false);
            });
    }, []);

    useEffect(() => {
        load();

        const interval = window.setInterval(load, 5 * 60 * 1000);

        return () => window.clearInterval(interval);
    }, [load]);

    return (
        <div className="flex h-full flex-col overflow-y-auto overflow-x-visible p-2">
            {loading && items.length === 0 ? (
                Array.from({ length: 6 }).map((_, i) => (
                    <NewsCardSkeleton key={i} index={i} />
                ))
            ) : error ? (
                <div className="px-2 py-6 text-center font-mono text-[11px] text-white/25">
                    Couldn't load news — retrying shortly
                </div>
            ) : items.length === 0 ? (
                <div className="px-2 py-6 text-center font-mono text-[11px] text-white/25">
                    No news available
                </div>
            ) : (
                <AnimatePresence initial={false}>
                    {items.map((item, i) => (
                        <NewsCard key={item.id} item={item} index={i} />
                    ))}
                </AnimatePresence>
            )}
        </div>
    );
}