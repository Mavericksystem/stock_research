import Header from "./Header";
import Sidebar from "./Sidebar";

export default function AppLayout({
  sidebarOpen,
  onToggleSidebar,
  onEventSelect,
  trackedStocksCount,
  children,
}) {
  return (
    <div className="layout">
      <Header
        stocksTracked={trackedStocksCount}
        sidebarOpen={sidebarOpen}
        onToggleSidebar={onToggleSidebar}
      />

      <div className="layout-body">
        <Sidebar
          open={sidebarOpen}
          onToggle={onToggleSidebar}
          onEventSelect={onEventSelect}
        />

        <div className="main-content">
          {children}
        </div>
      </div>
    </div>
  );
}