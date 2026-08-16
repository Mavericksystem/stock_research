import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import NewsPanel from "../features/news/NewsPanel";
import GraphsPanel from "../features/graphs/GraphsPanel";
import AnomaliesPanel from "../features/anomalies/AnomaliesPanel";

type Section = "news" | "graphs" | "anomalies";

interface RightRailProps {
    onEventSelect: (question: string) => void;
}

/**
 * Right-side drawer — News, Graphs, Anomalies as accordion sections
 * (exactly one open at a time, same as before). The whole rail is now
 * a slide-in drawer instead of a desktop-only fixed column, so it
 * works on mobile too — toggle tab is self-contained, no external
 * state needed from AppLayout/App.
 */
export default function RightRail({ onEventSelect }: RightRailProps) {
    const [drawerOpen, setDrawerOpen] = useState(false);
    const [section, setSection] = useState<Section>("news");
    const drawerWidth = "min(320px, 85vw)";

    const sections: { key: Section; label: string }[] = [
        { key: "news", label: "NEWS" },
        { key: "graphs", label: "GRAPHS" },
        { key: "anomalies", label: "ANOMALIES" },
    ];

    return (
        <>
            {/* Toggle tab — slides with the drawer, retracts on click */}
            <motion.button
                type="button"
                aria-label={drawerOpen ? "Close panel" : "Open panel"}
                onClick={() => setDrawerOpen((v) => !v)}
                animate={{ x: drawerOpen ? `calc(-1 * ${drawerWidth})` : 0 }}
                transition={{ type: "spring", stiffness: 360, damping: 36, mass: 0.8 }}
                className="fixed right-0 top-1/2 z-[1201] flex h-14 w-5 -translate-y-1/2 items-center justify-center rounded-l-md border border-r-0 border-white/[0.06] bg-white/[0.07]"
            >
                <motion.span
                    animate={{ rotate: drawerOpen ? 180 : 0 }}
                    transition={{ duration: 0.2 }}
                    className="text-white/50"
                >
                    ‹
                </motion.span>
            </motion.button>

            {/* Mobile backdrop */}
            <AnimatePresence>
                {drawerOpen && (
                    <motion.button
                        type="button"
                        aria-label="Close panel"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 0.2 }}
                        onClick={() => setDrawerOpen(false)}
                        className="fixed inset-0 z-[1100] bg-black/45 md:hidden"
                    />
                )}
            </AnimatePresence>

            {/* Drawer */}
            <AnimatePresence>
                {drawerOpen && (
                    <motion.aside
                        initial={{ x: "100%" }}
                        animate={{ x: 0 }}
                        exit={{ x: "100%" }}
                        transition={{ type: "spring", stiffness: 360, damping: 36, mass: 0.8 }}
                        className="fixed right-0 top-0 z-[1200] flex h-full w-[min(320px,85vw)] flex-col overflow-hidden border-l border-[var(--border)] bg-[#24211d] shadow-[-8px_0_30px_rgba(0,0,0,0.25)]"
                    >
                        {sections.map(({ key, label }) => (
                            <div
                                key={key}
                                className="flex flex-col overflow-hidden border-t border-[var(--border)] first:border-t-0"
                                style={{ flex: section === key ? 1 : "0 0 auto" }}
                            >
                                <button
                                    type="button"
                                    onClick={() => setSection(key)}
                                    className="flex shrink-0 items-center justify-between px-3.5 py-3 text-left"
                                >
                                    <span className="text-[13px] font-bold tracking-[0.08em] text-white">
                                        {label}
                                    </span>
                                    <motion.span
                                        animate={{ rotate: section === key ? 0 : -90 }}
                                        transition={{ duration: 0.15 }}
                                        className="text-white/40"
                                    >
                                        ▾
                                    </motion.span>
                                </button>

                                <motion.div
                                    animate={{ height: section === key ? "auto" : 0 }}
                                    initial={false}
                                    transition={{ duration: 0.2 }}
                                    className="overflow-hidden"
                                    style={{ flex: section === key ? 1 : "0 0 auto" }}
                                >
                                    {section === key && key === "news" && <NewsPanel />}
                                    {section === key && key === "graphs" && <GraphsPanel />}
                                    {section === key && key === "anomalies" && (
                                        <AnomaliesPanel onEventSelect={onEventSelect} />
                                    )}
                                </motion.div>
                            </div>
                        ))}
                    </motion.aside>
                )}
            </AnimatePresence>
        </>
    );
}