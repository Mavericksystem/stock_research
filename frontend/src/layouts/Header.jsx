export default function Header({ stocksTracked }) {
  return (
    <header className="header">
      <div className="header-left">
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