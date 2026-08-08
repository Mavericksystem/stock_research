import { useState } from "react";
import { motion } from "framer-motion";
import NewsPanel from "../../news/NewsPanel";

type Section = "news" | "graphs";

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
                ></button>
                <span className="text-[13px] font-bold tracking-[0.08em] text-white">
                    NEWS
                </span>
                <motion.span
                    animate={{ rotate: open === "news" ? 0 : -90 }}
                    transition={{ duration: 0.15 }}
                    className="text-white/40"
                ></motion.span>
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
      </div >