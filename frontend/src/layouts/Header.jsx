export default function Header({ stocksTracked, sidebarOpen, onToggleSidebar }) {
  return (
    <header className="header">
      <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
        <button
          className="ec-toggle"
          onClick={onToggleSidebar}
          style={{ position: "relative", zIndex: 1200 }}
          aria-label={sidebarOpen ? "Close sidebar" : "Open sidebar"}
        >
          ☰
        </button>
        <div className="header-logo">
          <div className="header-logo-mark">M²</div>
          <span className="header-logo-name">Market Mind</span>
        </div>
      </div>

      <div className="header-status">
        <span className="status-dot" />
        {stocksTracked} STOCKS TRACKED
      </div>
    </header>
  );
}