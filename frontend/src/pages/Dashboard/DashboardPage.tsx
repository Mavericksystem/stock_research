import { AnimatePresence, motion } from "framer-motion";
import type { ChangeEvent, KeyboardEvent, RefObject } from "react";
import type { Message, Source, ToolStep } from "../../lib/api-client";

interface DashboardPageProps {
  messages: Message[];
  loading: boolean;
  steps: ToolStep[];
  streamingAnswer: string;
  streamingSymbol: string | null;
  input: string;
  onInputChange: (value: string) => void;
  onKeyDown: (event: KeyboardEvent<HTMLTextAreaElement>) => void;
  onSubmit: () => void;
  onSuggestion: (suggestion: string) => void;
  onStock: (symbol: string) => void;
  bottomRef: RefObject<HTMLDivElement | null>;
  textareaRef: RefObject<HTMLTextAreaElement | null>;
  suggestions: readonly string[];
  trackedStocks: readonly string[];
}

function EventBadge({
  eventType,
  magnitude,
}: {
  eventType?: string | null;
  magnitude?: number | null;
}) {
  if (!eventType) return null;

  const isSpike = eventType.includes("SPIKE");
  const isDrop = eventType.includes("DROP");
  const label = isSpike ? "▲ SPIKE" : isDrop ? "▼ DROP" : eventType;
  const mag =
    magnitude != null
      ? ` ${magnitude > 0 ? "+" : ""}${magnitude.toFixed(2)}%`
      : "";

  return (
    <span
      className={`rounded px-2 py-[3px] font-mono text-[11px] font-medium tracking-[0.5px] ${isSpike
        ? "border border-emerald-400/25 bg-emerald-400/10 text-[var(--green)]"
        : isDrop
          ? "border border-red-400/25 bg-red-400/10 text-[var(--red)]"
          : "border border-[var(--amber-border)] bg-[var(--amber-dim)] text-[var(--amber)]"
        }`}
    >
      {label}
      {mag}
    </span>
  );
}

function SourceCard({ source }: { source: Source }) {
  const score =
    source.relevance_score != null
      ? source.relevance_score.toFixed(2)
      : "—";

  const card = (
    <motion.div
      whileHover={{ x: 2 }}
      transition={{ duration: 0.15 }}
      className="flex items-start gap-2.5 rounded-[var(--radius)] border border-[var(--border-soft)] bg-[var(--surface)] px-3 py-2.5 transition-colors hover:border-[var(--amber-border)]"
    >
      <span className="mt-px min-w-7 shrink-0 font-mono text-[10px] text-[var(--amber)] opacity-80">
        {score}
      </span>
      <div className="min-w-0 flex-1">
        <span className="block truncate text-[13px] text-[var(--text)]">
          {source.title ?? "Untitled"}
        </span>
        <div className="mt-0.5 font-mono text-[10px] text-[var(--text-muted)]">
          {source.source ?? "unknown source"}
        </div>
      </div>
    </motion.div>
  );

  if (!source.url) return card;

  return (
    <a
      href={source.url}
      target="_blank"
      rel="noopener noreferrer"
      className="block no-underline"
    >
      {card}
    </a>
  );
}

function AssistantMessage({ msg }: { msg: Extract<Message, { type: "assistant" }> }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.28, ease: "easeOut" }}
      className="flex w-full flex-col gap-3"
    >
      <div className="mb-1 flex items-center gap-2.5">
        <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-[var(--amber)] font-mono text-[10px] font-medium text-[#080c10]">
          M
        </div>
        {msg.symbol && (
          <span className="font-mono text-[11px] font-medium text-[var(--amber)] opacity-90">
            {msg.symbol}
          </span>
        )}
        <EventBadge eventType={msg.event_type} magnitude={msg.magnitude} />
        {msg.event_date && (
          <span className="font-mono text-[11px] text-[var(--text-muted)]">
            {msg.event_date}
          </span>
        )}
      </div>

      {msg.error ? (
        <div className="pl-[34px] font-mono text-[13px] text-[var(--red)]">
          {msg.error}
        </div>
      ) : (
        <p className="max-w-[75ch] whitespace-pre-line pl-[34px] text-[14.5px] leading-[1.75] text-[var(--text)]">
          {msg.answer}
        </p>
      )}

      {msg.sources.length > 0 && (
        <div className="max-w-[75ch] pl-[34px]">
          <div className="mb-2 font-mono text-[10px] uppercase tracking-[1px] text-[var(--text-dim)]">
            Sources
          </div>
          <div className="flex flex-col gap-1.5">
            {msg.sources.map((source, index) => (
              <SourceCard key={`${source.url ?? source.title}-${index}`} source={source} />
            ))}
          </div>
        </div>
      )}
    </motion.div>
  );
}

function TypingIndicator() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="flex items-center gap-2.5"
    >
      <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-[var(--amber)] font-mono text-[10px] font-medium text-[#080c10]">
        M
      </div>
      <div className="flex gap-1 pl-1">
        {[0, 1, 2].map((index) => (
          <motion.span
            key={index}
            animate={{ opacity: [0.2, 1, 0.2], y: [0, -2, 0] }}
            transition={{
              duration: 1.2,
              repeat: Infinity,
              delay: index * 0.2,
              ease: "easeInOut",
            }}
            className="h-[5px] w-[5px] rounded-full bg-[var(--text-muted)]"
          />
        ))}
      </div>
    </motion.div>
  );
}

function ToolSteps({ steps }: { steps: ToolStep[] }) {
  if (steps.length === 0) return null;

  return (
    <div className="flex flex-col gap-2 pl-[34px]">
      <div className="font-mono text-[10px] uppercase tracking-[0.8px] text-[var(--text-dim)]">
        Working
      </div>
      <div className="flex flex-col gap-1.5">
        <AnimatePresence initial={false}>
          {steps.map((step) => (
            <motion.div
              key={step.id}
              initial={{ opacity: 0, x: -4 }}
              animate={{ opacity: step.status === "done" ? 0 : 1, x: 0 }}
              exit={{ opacity: 0, x: 4 }}
              transition={{ duration: 0.2 }}
              className={`flex items-center gap-2 font-mono text-[11px] ${step.status === "done"
                ? "text-[var(--green)]"
                : "text-[var(--text-muted)]"
                }`}
            >
              <motion.span
                animate={
                  step.status === "running"
                    ? { rotate: 360 }
                    : { rotate: 0 }
                }
                transition={
                  step.status === "running"
                    ? { duration: 0.9, repeat: Infinity, ease: "linear" }
                    : { duration: 0.15 }
                }
                className={`h-2.5 w-2.5 shrink-0 rounded-full border ${step.status === "running"
                  ? "border-[var(--amber-border)] border-t-[var(--amber)]"
                  : "border-[var(--green)] bg-[var(--green)]"
                  }`}
              />
              <span>{step.label}</span>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}

function EmptyState({
  onSuggestion,
  onStock,
  suggestions,
  trackedStocks,
}: {
  onSuggestion: (suggestion: string) => void;
  onStock: (symbol: string) => void;
  suggestions: readonly string[];
  trackedStocks: readonly string[];
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, ease: "easeOut" }}
      className="m-auto text-center"
    >
      <div className="mb-2 text-[22px] font-semibold tracking-[-0.5px] text-[var(--text)]">
        Market Mind
      </div>
      <div className="shine-text mb-8 text-sm">
        Ask why any stock moved. Get a sourced explanation.
      </div>

      <div className="mb-4 flex flex-wrap justify-center gap-2">
        {suggestions.map((suggestion) => (
          <motion.button
            key={suggestion}
            type="button"
            whileHover={{ y: -1 }}
            whileTap={{ scale: 0.97 }}
            onClick={() => onSuggestion(suggestion)}
            className="suggestion-card"
          >
            <span className="suggestion-size">
              {suggestion}
            </span>

            <span className="suggestion-border" />

            <p
              className="suggestion-text"
              data-title={suggestion}
              data-text="Know more"
            />
          </motion.button>
        ))}
      </div>

      <div className="mb-3 mt-2 font-mono text-xs text-[var(--text-dim)]">
        TRACKED STOCKS
      </div>
      <div className="flex flex-wrap justify-center gap-2">
        {trackedStocks.map((symbol) => (
          <motion.button
            key={symbol}
            type="button"
            whileHover={{
              x: -2,
              y: -4,
            }}
            whileTap={{
              x: 1,
              y: 2,
            }}
            transition={{
              type: "spring",
              stiffness: 500,
              damping: 25,
            }}
            onClick={() => onStock(symbol)}
            className="
    rounded-md
    border border-[var(--border)]
    bg-[var(--surface)]
    px-3 py-1.5
    font-mono text-xs font-medium
    text-[var(--text-muted)]
    shadow-[0_0_0_0_transparent]
    hover:shadow-[2px_5px_0_0_var(--border)]
  "
          >
            {symbol}
          </motion.button>
        ))}
      </div>
    </motion.div>
  );
}

function SendIcon() {
  return (
    <svg
      viewBox="0 0 16 16"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
      className="h-3.5 w-3.5 fill-[#080c10]"
    >
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
}: DashboardPageProps) {
  const handleInput = (event: ChangeEvent<HTMLTextAreaElement>) => {
    onInputChange(event.target.value);
  };

  return (
    <>
      <div className="flex min-h-0 flex-1 flex-col items-center gap-6 overflow-y-auto px-3 pb-2 pt-6 md:px-6">
        {messages.length === 0 && !loading ? (
          <EmptyState
            onSuggestion={onSuggestion}
            onStock={onStock}
            suggestions={suggestions}
            trackedStocks={trackedStocks}
          />
        ) : (
          <div className="content-width flex flex-col gap-6">
            {messages.map((msg) => (
              <div key={msg.id} className="w-full">
                {msg.type === "user" ? (
                  <motion.div
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.25 }}
                    className="flex justify-start"
                  >
                    <div className="w-fit max-w-[520px] rounded-2xl border border-[var(--border)] bg-[var(--surface-2)] px-[18px] py-3.5 text-[var(--text)]">
                      {msg.content}
                    </div>
                  </motion.div>
                ) : (
                  <AssistantMessage msg={msg} />
                )}
              </div>
            ))}

            {loading && (
              <div className="w-full">
                <div className="flex w-full flex-col gap-3">
                  <div className="mb-1 flex items-center gap-2.5">
                    <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-[var(--amber)] font-mono text-[10px] font-medium text-[#080c10]">
                      M
                    </div>
                    {streamingSymbol && (
                      <span className="font-mono text-[11px] font-medium text-[var(--amber)] opacity-90">
                        {streamingSymbol}
                      </span>
                    )}
                  </div>
                  <ToolSteps steps={steps} />
                  {streamingAnswer ? (
                    <p className="max-w-[75ch] whitespace-pre-line pl-[34px] text-[14.5px] leading-[1.75] text-[var(--text)]">
                      {streamingAnswer}
                    </p>
                  ) : (
                    <div className="pl-[34px]">
                      <TypingIndicator />
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="content-width mx-auto shrink-0 px-3 pb-4 pt-2 md:px-0 md:pb-6">
        <div className="flex min-h-[58px] items-end gap-3 rounded-2xl border border-[var(--border)] bg-[var(--surface-2)] px-[18px] py-3.5 transition-shadow focus-within:border-[#7c6f63] focus-within:shadow-[0_0_0_2px_rgba(245,242,236,0.05)]">
          <textarea
            ref={textareaRef}
            rows={1}
            placeholder="Ask why a stock moved…"
            value={input}
            onChange={handleInput}
            onKeyDown={onKeyDown}
            disabled={loading}
            className="max-h-[120px] min-h-[22px] flex-1 resize-none overflow-y-auto border-none bg-transparent text-sm leading-6 text-[var(--text)] outline-none placeholder:text-[var(--text-dim)] disabled:cursor-not-allowed disabled:opacity-60"
          />

          <motion.button
            type="button"
            whileHover={!loading && input.trim() ? { opacity: 0.88 } : undefined}
            whileTap={!loading && input.trim() ? { scale: 0.94 } : undefined}
            onClick={onSubmit}
            disabled={loading || !input.trim()}
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[var(--amber)] transition-opacity disabled:cursor-not-allowed disabled:opacity-35"
            aria-label="Send message"
          >
            <SendIcon />
          </motion.button>
        </div>
        <div className="mt-2 text-center font-mono text-[11px] text-[var(--text-dim)]">
          Enter to send · Shift+Enter for new line
        </div>
      </div>
    </>
  );
}
