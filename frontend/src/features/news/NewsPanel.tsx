import { useCallback, useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { fetchLatestNews, timeAgo, type NewsItem } from "./api";

function NewsCardSkeleton({ index }: { index: number }) {
    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: index * 0.03, duration: 0.2 }}