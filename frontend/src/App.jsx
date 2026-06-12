import { useState, useRef, useEffect, useCallback } from "react";
import { askQuestion } from "./api";
import EventsSidebar from "./EventsSidebar";
import "./sidebar.css";
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

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

const TOOL_LABELS = {
  get_event_details: "Fetching event details",
  get_technical_state: "Reading technical state",
  get_news_context: "Retrieving news context",
  get_price_history: "Loading price history",
};

function extractSymbol(question) {
  if (!question) return null;

  const words = String(question).toUpperCase().match(/\b[A-Z]{1,10}\b/g) ?? [];
  const stop = new Set([
    "A",
    "AN",
    "THE",
    "WHY",
    "WHAT",
    "WHEN",
    "WHERE",
    "WHO",
    "HOW",
    "DID",
    "DO",
    "DOES",
    "IS",
    "ARE",
    "WAS",
    "WERE",
    "DROP",
    "DROPPED",
    "FALL",
    "FELL",
    "FALLING",
    "SPIKE",
    "SPIKED",
    "MOVE",
    "MOVED",
    "RECENT",
    "RECENTLY",
    "LAST",
    "TODAY",
    "YESTERDAY",
    "TOMORROW",
    "STOCK",
    "PRICE",
    "EXPLAIN",
  ]);

  const candidates = words.filter((w) => !stop.has(w) && w.length >= 2);
  return candidates.length > 0 ? candidates[candidates.length - 1] : null;
}

function safeJsonParse(value) {
  if (value == null) return null;
  if (typeof value === "object") return value;
  if (typeof value !== "string") return null;
  try {
    return JSON.parse(value);
  } catch {
    return null;
  }
}

function normalizeStreamResult(payload, fallbackSymbol) {
  const symbol = payload?.symbol ?? fallbackSymbol ?? null;
  const explanation = payload?.explanation ?? {};

  let answer = "";
  if (Array.isArray(explanation.explanation)) {
    answer = explanation.explanation.filter(Boolean).join("\n\n");
  } else if (typeof explanation.explanation === "string") {
    answer = explanation.explanation;
  } else if (typeof explanation.primary_cause === "string") {
    answer = explanation.primary_cause;
  } else {
    answer = "";
  }

  let sources = [];
  const toolCalls = payload?.tool_calls_made;
  if (Array.isArray(toolCalls)) {
    const newsCall = toolCalls.find((c) => c?.tool === "get_news_context");
    const parsed = safeJsonParse(newsCall?.result);
    if (parsed?.articles && Array.isArray(parsed.articles)) {
      sources = parsed.articles.map((a) => ({
        title: a.title ?? null,
        source: a.source ?? null,
        url: a.url ?? null,
        relevance_score: a.relevance_score ?? a.score ?? null,
      }));
    }
  }

  return {
    answer,
    symbol,
    event_type: payload?.event_type ?? null,
    event_date: payload?.event_date ?? null,
    magnitude: payload?.magnitude ?? null,
    sources,
  };
}

// ── Sub-components ─────────────────────────────────────────────────────────

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
      <div style={{
        marginTop: 8, fontSize: 12, color: "var(--text-dim)",
        fontFamily: "var(--font-mono)", marginBottom: 12
      }}>
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
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [steps, setSteps] = useState([]);
  const [streamingAnswer, setStreamingAnswer] = useState("");
  const [streamingSymbol, setStreamingSymbol] = useState(null);
  const bottomRef = useRef(null);
  const textareaRef = useRef(null);

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
    setSteps([]);
    setStreamingAnswer("");
    setStreamingSymbol(null);

    const addStep = (tool) => {
      const label = TOOL_LABELS[tool] ?? tool;
      setSteps((prev) => {
        if (prev.some((s) => s.tool === tool && s.status === "running")) {
          return prev;
        }
        return [...prev, { id: uid(), tool, label, status: "running" }];
      });
    };

    const completeStep = (tool) => {
      setSteps((prev) =>
        prev.map((s) => (s.tool === tool && s.status === "running"
          ? { ...s, status: "done" }
          : s))
      );
      setTimeout(() => {
        setSteps((prev) => prev.filter((s) => !(s.tool === tool && s.status === "done")));
      }, 250);
    };

    const runStream = async () => {
      const symbol = extractSymbol(q) ?? "AAPL";
      setStreamingSymbol(symbol);

      const res = await fetch(`${API_BASE}/api/v1/ask/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q, symbol }),
      });

      if (!res.ok || !res.body) {
        throw new Error("Streaming request failed");
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const raw = line.slice(6).trim();
          if (!raw) continue;
          if (raw === "[DONE]") return;

          let event;
          try {
            event = JSON.parse(raw);
          } catch {
            continue;
          }

          if (event.type === "tool_call") {
            if (event.status === "calling") addStep(event.tool);
            if (event.status === "done") completeStep(event.tool);
          }

          if (event.type === "token" && typeof event.content === "string") {
            setStreamingAnswer((prev) => (prev ? `${prev} ${event.content}` : event.content));
          }

          if (event.type === "metadata" && event.symbol) {
            setStreamingSymbol(event.symbol);
          }

          if (event.type === "result" && event.data) {
            const normalized = normalizeStreamResult(event.data, symbol);
            const assistantMsg = {
              id: uid(),
              type: "assistant",
              answer: normalized.answer,
              symbol: normalized.symbol,
              event_type: normalized.event_type,
              event_date: normalized.event_date,
              magnitude: normalized.magnitude,
              sources: normalized.sources ?? [],
            };
            setMessages((prev) => [...prev, assistantMsg]);
          }
        }
      }
    };

    try {
      await runStream();
    } catch (err) {
      try {
        const data = await askQuestion(q);
        const assistantMsg = {
          id: uid(),
          type: "assistant",
          answer: data.answer,
          symbol: data.symbol,
          event_type: data.event_type,
          event_date: data.event_date,
          magnitude: data.magnitude,
          sources: data.sources ?? [],
        };
        setMessages((prev) => [...prev, assistantMsg]);
      } catch (fallbackErr) {
        setMessages((prev) => [
          ...prev,
          { id: uid(), type: "assistant", error: fallbackErr.message, answer: null },
        ]);
      }
    } finally {
      setLoading(false);
      setStreamingAnswer("");
      setSteps([]);
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

      <div className="layout-body">

        <EventsSidebar
          open={sidebarOpen}
          onToggle={() => setSidebarOpen((v) => !v)}
          onEventSelect={(question) => submit(question)}
        />

        <div className="main-content">

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
      </div>
    </div>
  );
}
