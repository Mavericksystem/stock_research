import { useState } from "react";
import { motion } from "framer-motion";
import NewsPanel from "../features/news/NewsPanel";

type Section = "news" | "graphs";

/**
 * Desktop-only right rail. Two accordion sections — News and Graphs.
 * Exactly one is open at all times (clicking the open section's header
 * does nothing — there is no "both closed" state, by design).
 *
 * Graphs is a placeholder until that feature is built. It renders but
 * is disabled, so the accordion shape is in place without pretending
 * the feature exists yet.
 */
export default function RightRail() {
    const [open, setOpen] = useState<Section>("news");

    const select = (section: Section) => {
        if (section === "graphs") return; // not implemented yet — no-op
        setOpen(section);
    };

    return (
        <aside className="hidden h-full w-[320px] shrink-0 flex-col overflow-hidden border-l border-[var(--border)] md:flex">
            {/* News section */}
            <div className="flex flex-col overflow-hidden" style={{ flex: open === "news" ? 1 : "0 0 auto" }}>
                <button
                    type="button"
                    onClick={() => select("news")}
                    className="flex shrink-0 items-center justify-between border-b border-white/[0.05] px-3.5 py-3 text-left"
                >
                    <span className="text-[13px] font-bold tracking-[0.08em] text-white">
                        NEWS
                    </span>
                    <motion.span
                        animate={{ rotate: open === "news" ? 0 : -90 }}
                        transition={{ duration: 0.15 }}
                        className="text-white/40"
                    >
                        ▾
                    </motion.span>
                </button>

                <motion.div
                    animate={{ height: open === "news" ? "auto" : 0 }}
                    initial={false}
                    transition={{ duration: 0.2 }}
                    className="overflow-hidden"
                >
                    {open === "news" && <NewsPanel />}
                </motion.div>
            </div>

            {/* Graphs section — placeholder, disabled */}
            <div className="flex flex-col overflow-hidden border-t border-[var(--border)]" style={{ flex: open === "graphs" ? 1 : "0 0 auto" }}>
                <button
                    type="button"
                    onClick={() => select("graphs")}
                    disabled
                    title="Coming soon"
                    className="flex shrink-0 cursor-not-allowed items-center justify-between px-3.5 py-3 text-left opacity-40"
                >
                    <span className="text-[13px] font-bold tracking-[0.08em] text-white">
                        GRAPHS
                    </span>
                    <span className="font-mono text-[10px] text-white/40">soon</span>
                </button>
            </div>
        </aside>
    );
}