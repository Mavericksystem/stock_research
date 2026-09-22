import { motion } from "framer-motion";
import { PanelRight, PanelRightClose } from "lucide-react";

import marketMindLogo from "@/assets/logo.png";
import { SidebarTrigger, useSidebar } from "@/components/ui/sidebar";

function HeaderSidebarTrigger() {
  const { open, openMobile, isMobile } = useSidebar();

  const expanded = isMobile ? openMobile : open;

  return (
    <SidebarTrigger className="text-[var(--text-muted)] hover:bg-white/[0.05] hover:text-[var(--text)]">
      {expanded ? (
        <PanelRightClose className="size-4" />
      ) : (
        <PanelRight className="size-4" />
      )}
    </SidebarTrigger>
  );
}

export default function Header() {
  return (
    <header className="relative z-20 flex shrink-0 items-center gap-3 border-b border-white/[0.06] bg-white/[0.015] px-3 py-3.5 shadow-[0_1px_8px_rgba(0,0,0,0.18)] md:px-6 md:py-[18px]">
      <div className="flex min-w-0 items-center gap-2.5">
        <motion.div
          initial={{ scale: 0.92, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.3, ease: "easeOut" }}
          className="relative flex h-7 w-11 shrink-0 items-center justify-center"
        >
          <img
            src={marketMindLogo}
            alt="Market Mind"
            className="absolute h-9 w-11 object-cover"
          />
        </motion.div>

        <span className="truncate text-[15px] font-semibold tracking-[-0.3px] text-[var(--text)]">
          Market Mind
        </span>
      </div>

      <div className="ml-auto flex shrink-0 items-center gap-3">
        <div className="md:hidden">
          <HeaderSidebarTrigger />
        </div>
      </div>
    </header>
  );
}