import { useState, useRef, useEffect, useCallback } from "react";
import { askQuestion } from "./api";

// ── Constants ──────────────────────────────────────────────────────────────

const STOCKS = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "JPM", "V", "WMT"];

const SUGGESTIONS = [
  "Why did NVDA drop recently?",
  "What caused Apple's last spike?",
  "Explain Tesla's latest move",
  "What's driving Meta's price?",
];

let msgId = 0;
const uid = () => ++msgId;

// ── Sub-components ─────────────────────────────────────────────────────────

function EventBadge({ eventType, magnitude }) {
  if (!eventType) return null;

  const isSpike = eventType.includes("SPIKE");
  const isDrop  = eventType.includes("DROP");

  const cls = isSpike
    ? "event-badge event-badge-spike"
    : isDrop
    ? "event-badge event-badge-drop"
    : "event-badge event-badge-neutral";

  const label = isSpike ? "▲ SPIKE" : isDrop ? "▼ DROP" : eventType;
  const mag   = magnitude != null ? ` ${magnitude > 0 ? "+" : ""}${magnitude.toFixed(2)}%` : "";

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
      <a href={source.url} target="_blank" rel="noopener noreferrer"
         style={{ textDecoration: "none" }}>
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
            {msg.sources.map((s, i) => (
              <SourceCard key={i} source={s} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="message typing">
      <div className="assistant-icon">M</div>
      <div className="typing-dots">
        <span /><span /><span />
      </div>
    </div>
  );
}

function EmptyState({ onSuggestion, onStock }) {
  return (
    <div className="empty-state">
      <div className="empty-title">Market Mind</div>
      <div className="empty-sub">
        Ask why any stock moved. Get a sourced explanation.
      </div>
      <div className="stock-pills" style={{ marginBottom: 16 }}>
        {SUGGESTIONS.map((s) => (
          <button key={s} className="stock-pill" onClick={() => onSuggestion(s)}
                  style={{ fontSize: 13, padding: "7px 14px" }}>
            {s}
          </button>
        ))}
      </div>
      <div style={{ marginTop: 8, fontSize: 12, color: "var(--text-dim)",
                    fontFamily: "var(--font-mono)", marginBottom: 12 }}>
        TRACKED STOCKS
      </div>
      <div className="stock-pills">
        {STOCKS.map((sym) => (
          <button key={sym} className="stock-pill"
                  onClick={() => onStock(sym)}>
            {sym}
          </button>
        ))}
      </div>
    </div>
  );
}

// ── SendIcon ───────────────────────────────────────────────────────────────

function SendIcon() {
  return (
    <svg viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg">
      <path d="M1 1l14 7-14 7V9.5l10-1.5-10-1.5V1z" />
    </svg>
  );
}

// ── Main App ───────────────────────────────────────────────────────────────

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput]       = useState("");
  const [loading, setLoading]   = useState(false);
  const bottomRef               = useRef(null);
  const textareaRef             = useRef(null);

  // Auto-scroll to latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // Auto-resize textarea
  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = Math.min(ta.scrollHeight, 120) + "px";
  }, [input]);

  const submit = useCallback(async (question) => {
    const q = question.trim();
    if (!q || loading) return;

    const userMsg = { id: uid(), type: "user", content: q };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const data = await askQuestion(q);
      const assistantMsg = {
        id: uid(),
        type: "assistant",
        answer:      data.answer,
        symbol:      data.symbol,
        event_type:  data.event_type,
        event_date:  data.event_date,
        magnitude:   data.magnitude,
        sources:     data.sources ?? [],
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { id: uid(), type: "assistant", error: err.message, answer: null },
      ]);
    } finally {
      setLoading(false);
    }
  }, [loading]);

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit(input);
    }
  };

  const handleStockPill = (sym) => {
    submit(`Why did ${sym} move recently?`);
  };

  const handleSuggestion = (s) => {
    submit(s);
  };

  return (
    <div className="layout">
      {/* Header */}
      <header className="header">
        <div className="header-logo">
          <div className="header-logo-mark">M²</div>
          <span className="header-logo-name">Market Mind</span>
        </div>
        <div className="header-status">
          <span className="status-dot" />
          {STOCKS.length} STOCKS TRACKED
        </div>
      </header>

      {/* Chat area */}
      <div className="chat-area">
        {messages.length === 0 && !loading ? (
          <EmptyState onSuggestion={handleSuggestion} onStock={handleStockPill} />
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

        {loading && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="input-bar">
        <div className="input-wrap">
          <textarea
            ref={textareaRef}
            className="input-field"
            rows={1}
            placeholder="Ask why a stock moved…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKey}
            disabled={loading}
          />
          <button
            className="send-btn"
            onClick={() => submit(input)}
            disabled={loading || !input.trim()}
          >
            <SendIcon />
          </button>
        </div>
        <div className="input-hint">Enter to send · Shift+Enter for new line</div>
      </div>
    </div>
  );
}
