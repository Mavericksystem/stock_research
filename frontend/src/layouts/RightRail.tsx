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
        <aside className="hidden h-full w-[320px] shrink-0 flex-col overflow-hidden border-l border-[var(--border)] md:flex"></aside>