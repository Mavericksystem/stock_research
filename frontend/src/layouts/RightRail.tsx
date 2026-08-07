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