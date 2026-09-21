import type { CSSProperties, ReactNode } from "react";

import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";

import Header from "./Header";
import RightRail from "./RightRail";
import { RailProvider } from "./rail/rail-context";

interface AppLayoutProps {
  onEventSelect: (question: string) => void;
  trackedStocksCount: number;
  children: ReactNode;
}

/**
 * Shell.
 *
 * SidebarProvider is the top-level flex row: the desktop rail is
 * `position: fixed`, and the space it reserves in flow comes from the
 * sidebar-gap element, so the provider has to own the viewport and the header
 * has to live inside SidebarInset.
 *
 * `--sidebar-width` is intentionally the *collapsed* width. Both it and
 * `--sidebar-width-icon` are 3.5rem, which pins the in-flow gap at 3.5rem in
 * every state; RightRail then grows only the fixed container to `--rail-width`.
 * Net effect: the chat column never reflows and the rail behaves like an
 * overlay drawer on desktop, matching the mobile sheet.
 *
 * `--sidebar-width-mobile` is deliberately NOT set here — the mobile sheet is
 * portalled to <body> and would not inherit it. It lives on :root in index.css.
 *
 * Below the `md` breakpoint the rail has no entry point at all: no header
 * trigger, no mobile icon strip. `<Sidebar>` still mounts (as a closed Sheet)
 * so the desktop↔mobile transition on resize stays stateful, but nothing
 * research-related is on screen — the chat column gets the full viewport.
 */
export default function AppLayout({
  onEventSelect,
  trackedStocksCount,
  children,
}: AppLayoutProps) {
  return (
    <SidebarProvider
      defaultOpen={false}
      className="h-dvh min-h-0 overflow-hidden bg-[var(--bg)]"
      style={
        {
          "--sidebar-width": "3.5rem",
          "--sidebar-width-icon": "3.5rem",
          "--rail-width": "min(22rem, 92vw)",
        } as CSSProperties
      }
    >
      <RailProvider>
        <SidebarInset className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden bg-[var(--bg)]">
          <Header stocksTracked={trackedStocksCount} />

          <div className="flex min-h-0 flex-1">
            <div className="relative flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden px-3 md:px-6">
              {children}
            </div>

            {/* No mobile icon strip. Desktop gets its icon strip from the
                collapsed sidebar itself; mobile intentionally gets nothing. */}
          </div>
        </SidebarInset>

        {/* After the inset so the desktop gap reserves space on the right. */}
        <RightRail onEventSelect={onEventSelect} />
      </RailProvider>
    </SidebarProvider>
  );
}
