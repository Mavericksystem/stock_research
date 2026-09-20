import { motion } from "framer-motion";
import { PanelRight, PanelRightClose } from "lucide-react";

import { SidebarTrigger, useSidebar } from "@/components/ui/sidebar";

interface HeaderProps {
  stocksTracked: number;
}

/**
 * The ONLY rail trigger in the app lives here. It used to be duplicated
 * (this one, plus a second SidebarTrigger inside RightRail's own
 * SidebarHeader) — that second one has been removed. This one has to stay
 * in the header specifically because on mobile the rail renders as a closed
 * Sheet: a trigger placed *inside* the Sheet is invisible until the Sheet is
 * already open, so it can never be the thing that opens it. The header is
 * outside the Sheet on every breakpoint, so it's the only place a trigger
 * can actually do its job on mobile.
 */
function HeaderSidebarTrigger() {
  const { open, openMobile, isMobile } = useSidebar();

  // `open` is the desktop state only — on mobile the rail is a sheet driven by
  // `openMobile`, so reading `open` there shows the wrong icon.
  const expanded = isMobile ? openMobile : open;

  return (
    <SidebarTrigger
      aria-label={expanded ? "Collapse research panel" : "Open research panel"}
      className="text-[var(--text-muted)] hover:bg-white/[0.05] hover:text-[var(--text)]"
    >
      {expanded ? (
        <PanelRightClose className="size-4" />
      ) : (
        <PanelRight className="size-4" />
      )}
    </SidebarTrigger>
  );
}

export default function Header({ stocksTracked }: HeaderProps) {
  return (
    <header className="relative z-20 flex shrink-0 items-center gap-3 border-b border-[var(--border)] px-3 py-3.5 md:px-6 md:py-[18px]">
      <div className="flex min-w-0 items-center gap-2.5">
        <motion.div
          initial={{ scale: 0.92, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.3, ease: "easeOut" }}
          className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-[var(--amber)] font-mono text-[13px] font-medium tracking-[-0.5px] text-[#080c10]"
        >
          M²
        </motion.div>
        <span className="truncate text-[15px] font-semibold tracking-[-0.3px] text-[var(--text)]">
          Market Mind
        </span>
      </div>

      <div className="ml-auto flex shrink-0 items-center gap-3">
        <div className="flex items-center gap-1.5 font-mono text-[10px] text-[var(--text-muted)] md:text-[11px]">
          <motion.span
            aria-hidden="true"
            animate={{ opacity: [1, 0.4, 1] }}
            transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
            className="h-1.5 w-1.5 rounded-full bg-[var(--green)]"
          />
          <span>{stocksTracked} STOCKS TRACKED</span>
        </div>

        <HeaderSidebarTrigger />
      </div>
    </header>
  );
}
