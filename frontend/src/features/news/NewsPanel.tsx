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
        ></motion.div>