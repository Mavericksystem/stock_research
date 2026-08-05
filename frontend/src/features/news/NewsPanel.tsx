import { useCallback, useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { fetchLatestNews, timeAgo, type NewsItem } from "../api";

function NewsCardSkeleton({ index }: { index: number }) {
    return (