import type { ReactNode } from "react";
import Header from "./Header";
import Sidebar from "./Sidebar";
import RightRail from "./RightRail";

interface AppLayoutProps {
  sidebarOpen: boolean;
  onToggleSidebar: () => void;
  onEventSelect: (question: string) => void;
  trackedStocksCount: number;
  children: ReactNode;
}

export default function AppLayout({
  sidebarOpen,
  onToggleSidebar,
  onEventSelect,
  trackedStocksCount,
  children,
}: AppLayoutProps) {
  return (
    <div className="flex h-dvh w-full flex-col bg-[var(--bg)] px-3 md:px-6">
      <Header stocksTracked={trackedStocksCount} />

      <div className="relative flex min-h-0 flex-1 overflow-hidden">
        {/* Left rail */}
        <aside className="hidden w-[280px] shrink-0 md:block">
          <Sidebar
            open={sidebarOpen}
            onToggle={onToggleSidebar}
            onEventSelect={onEventSelect}
          />
        </aside>

        {/* Center */}
        <main className="relative flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
          {children}
        </main>

        {/* Right rail */}
        <RightRail />
      </div>
    </div>
  );
}