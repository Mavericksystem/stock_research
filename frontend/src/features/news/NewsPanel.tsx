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