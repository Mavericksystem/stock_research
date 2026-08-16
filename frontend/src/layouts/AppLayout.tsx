import type { ReactNode } from "react";
import Header from "./Header";
import RightRail from "./RightRail";

interface AppLayoutProps {
  onEventSelect: (question: string) => void;
  trackedStocksCount: number;
  children: ReactNode;
}

export default function AppLayout({
  onEventSelect,
  trackedStocksCount,
  children,
}: AppLayoutProps) {
  return (
    <div className="flex h-dvh w-full flex-col bg-[var(--bg)] px-3 md:px-6">
      <Header stocksTracked={trackedStocksCount} />

      <div className="relative flex min-h-0 flex-1 overflow-hidden">
        {/* Center */}
        <main className="relative flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
          {children}
        </main>

        {/* Right drawer — News / Graphs / Anomalies, mobile + desktop */}
        <RightRail onEventSelect={onEventSelect} />
      </div>
    </div>
  );
}