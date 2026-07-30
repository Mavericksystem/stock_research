function EventBadge({ eventType, magnitude }) {
  if (!eventType) return null;

  const isSpike = eventType.includes("SPIKE");
  const isDrop = eventType.includes("DROP");

  const cls = isSpike
    ? "event-badge event-badge-spike"
    : isDrop
      ? "event-badge event-badge-drop"
      : "event-badge event-badge-neutral";

  const label = isSpike ? "▲ SPIKE" : isDrop ? "▼ DROP" : eventType;
  const mag = magnitude != null ? ` ${magnitude > 0 ? "+" : ""}${magnitude.toFixed(2)}%` : "";

  return <span className={cls}>{label}{mag}</span>;
}

function SourceCard({ source }) {
  const score = source.relevance_score != null
    ? source.relevance_score.toFixed(2)
    : "—";

  const inner = (
    <div className="source-card" style={source.url ? {} : { cursor: "default" }}>
      <span className="source-score">{score}</span>
      <div className="source-body">
        <span className="source-title">{source.title ?? "Untitled"}</span>
        <div className="source-meta">{source.source ?? "unknown source"}</div>
      </div>
    </div>
  );

  if (source.url) {
    return (
      <a href={source.url} target="_blank" rel="noopener noreferrer" style={{ textDecoration: "none" }}>
        {inner}
      </a>
    );
  }

  return inner;
}

function AssistantMessage({ msg }) {
  return (
    <div className="message message-assistant">
      <div className="message-assistant-header">
        <div className="assistant-icon">M</div>
        {msg.symbol && (
          <span className="event-meta" style={{ fontWeight: 500, color: "var(--amber)", opacity: 0.9 }}>
            {msg.symbol}
          </span>
        )}
        <EventBadge eventType={msg.event_type} magnitude={msg.magnitude} />
        {msg.event_date && (
          <span className="event-meta">{msg.event_date}</span>
        )}
      </div>

      {msg.error ? (
        <div className="error-msg">{msg.error}</div>
      ) : (
        <p className="message-answer">{msg.answer}</p>
      )}

      {msg.sources && msg.sources.length > 0 && (
        <div className="sources-section">
          <div className="sources-label">Sources</div>
          <div className="sources-list">
            {msg.sources.map((source, i) => (
              <SourceCard key={i} source={source} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function TypingIndicator({ inline = false }) {
  if (inline) {
    return (
      <div className="typing-dots">
        <span /><span /><span />
      </div>
    );
  }

  return (
    <div className="message typing">
      <div className="assistant-icon">M</div>
      <div className="typing-dots">
        <span /><span /><span />
      </div>
    </div>
  );
}

function ToolSteps({ steps }) {
  if (!steps || steps.length === 0) return null;

  return (
    <div className="tool-steps">
      <div className="tool-steps-title">Working</div>
      <div className="tool-steps-list">
        {steps.map((step) => (
          <div key={step.id} className={`tool-step tool-step-${step.status}`}>
            <span className="tool-step-indicator" />
            <span className="tool-step-label">{step.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function EmptyState({ onSuggestion, onStock, suggestions, trackedStocks }) {
  return (
    <div className="empty-state">
      <div className="empty-title">Market Mind</div>
      <div className="empty-sub">
        Ask why any stock moved. Get a sourced explanation.
      </div>
      <div className="stock-pills" style={{ marginBottom: 16 }}>
        {suggestions.map((suggestion) => (
          <button key={suggestion} className="stock-pill" onClick={() => onSuggestion(suggestion)} style={{ fontSize: 13, padding: "7px 14px" }}>
            {suggestion}
          </button>
        ))}
      </div>
      <div style={{
        marginTop: 8, fontSize: 12, color: "var(--text-dim)",
        fontFamily: "var(--font-mono)", marginBottom: 12,
      }}>
        TRACKED STOCKS
      </div>
      <div className="stock-pills">
        {trackedStocks.map((symbol) => (
          <button key={symbol} className="stock-pill" onClick={() => onStock(symbol)}>
            {symbol}
          </button>
        ))}
      </div>
    </div>
  );
}

function SendIcon() {
  return (
    <svg viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg">
      <path d="M1 1l14 7-14 7V9.5l10-1.5-10-1.5V1z" />
    </svg>
  );
}

export default function DashboardPage({
  messages,
  loading,
  steps,
  streamingAnswer,
  streamingSymbol,
  input,
  onInputChange,
  onKeyDown,
  onSubmit,
  onSuggestion,
  onStock,
  bottomRef,
  textareaRef,
  suggestions,
  trackedStocks,
}) {
  return (
    <>
      <div className="chat-area">
        {messages.length === 0 && !loading ? (
          <EmptyState
            onSuggestion={onSuggestion}
            onStock={onStock}
            suggestions={suggestions}
            trackedStocks={trackedStocks}
          />
        ) : (
          messages.map((msg) => (
            <div key={msg.id} className="message">
              {msg.type === "user" ? (
                <div className="message-user">
                  <div className="message-user-bubble">{msg.content}</div>
                </div>
              ) : (
                <AssistantMessage msg={msg} />
              )}
            </div>
          ))
        )}

        {loading && (
          <div className="message">
            <div className="message-assistant">
              <div className="message-assistant-header">
                <div className="assistant-icon">M</div>
                {streamingSymbol && (
                  <span className="event-meta" style={{ fontWeight: 500, color: "var(--amber)", opacity: 0.9 }}>
                    {streamingSymbol}
                  </span>
                )}
              </div>
              <ToolSteps steps={steps} />
              {streamingAnswer ? (
                <p className="message-answer">{streamingAnswer}</p>
              ) : (
                <TypingIndicator inline />
              )}
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="input-bar">
        <div className="input-wrap">
          <textarea
            ref={textareaRef}
            className="input-field"
            rows={1}
            placeholder="Ask why a stock moved…"
            value={input}
            onChange={(e) => onInputChange(e.target.value)}
            onKeyDown={onKeyDown}
            disabled={loading}
          />
          <button className="send-btn" onClick={onSubmit} disabled={loading || !input.trim()}>
            <SendIcon />
          </button>
        </div>
        <div className="input-hint">Enter to send · Shift+Enter for new line</div>
      </div>
    </>
  );
}