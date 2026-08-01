import type { ReactNode } from "react";
import Header from "./Header";
import Sidebar from "./Sidebar";

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
    <div className="flex h-dvh w-full flex-col bg-[var(--bg)] px-3 md:mx-auto md:max-w-[1440px] md:px-6">
      <Header stocksTracked={trackedStocksCount} />

      <div className="relative flex min-h-0 flex-1 overflow-hidden">
        <Sidebar
          open={sidebarOpen}
          onToggle={onToggleSidebar}
          onEventSelect={onEventSelect}
        />

        <main className="relative flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
          {children}
        </main>
      </div>
    </div>
  );
}
