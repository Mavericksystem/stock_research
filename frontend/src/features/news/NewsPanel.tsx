import { useCallback, useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { fetchLatestNews, timeAgo, type NewsItem } from "../api";

function NewsCardSkeleton({ index }: { index: number }) {
    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: index * 0.03, duration: 0.2 }}
            className="rounded-lg border border-[#3d3833] bg-[#2a2723] p-3"
        >
            <div className="mb-2 h-3 w-full animate-pulse rounded bg-white/[0.06]" />
            <div className="mb-2 h-3 w-3/4 animate-pulse rounded bg-white/[0.06]" />
            <div className="h-2.5 w-1/3 animate-pulse rounded bg-white/[0.04]" />
        </motion.div>
    );
}

function NewsCard({ item, index }: { item: NewsItem; index: number }) {
    return (
        <motion.a
            href={item.url}
            target="_blank"
            rel="noopener noreferrer"
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: Math.min(index * 0.02, 0.15), duration: 0.2 }}
            whileHover={{ x: 2 }}
            className="block rounded-lg border border-[#3d3833] bg-[#2a2723] p-3 no-underline transition-colors hover:border-[var(--amber-border)] hover:bg-[#322f2b]"
        >
            <div className="mb-1.5 flex items-center gap-1.5">
                <span className="rounded bg-[var(--amber-dim)] px-1.5 py-0.5 font-mono text-[10px] font-medium text-[var(--amber)]">
                    {item.symbol}
                </span>
            </div>
            <div className="mb-1.5 line-clamp-2 text-[13px] leading-snug text-[var(--text)]">
                {item.title}
            </div>
            <div className="flex items-center justify-between gap-2 font-mono text-[10px] text-[var(--text-dim)]">
                <span className="truncate">{item.source}</span>
                <span className="shrink-0">{timeAgo(item.published_at)}</span>
            </div>
        </motion.a>
    );
}

export default function NewsPanel() {
    const [items, setItems] = useState<NewsItem[]>([]);
    const [loading, setLoading] = useState(true);

    const load = useCallback(() => {
        setLoading(true);
        void fetchLatestNews(20).then((data) => {
            setItems(data);
            setLoading(false);
        });
    }, []);

    useEffect(() => {
        load();
        // Refresh in step with the backend poll interval (5 min) so the
        // panel doesn't go stale without a manual refresh.
        const interval = window.setInterval(load, 5 * 60 * 1000);
        return () => window.clearInterval(interval);
    }, [load]);

    return (
        <div className="flex h-full flex-col gap-2 overflow-y-auto p-2">
            {loading && items.length === 0 ? (
                Array.from({ length: 6 }).map((_, i) => (
                    <NewsCardSkeleton key={i} index={i} />
                ))
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