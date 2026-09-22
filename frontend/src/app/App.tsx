import { useCallback, useEffect, useRef, useState } from "react";
import { askQuestion, streamAskQuestion } from "../features/analysis/api";
import AppLayout from "../layouts/AppLayout";
import DashboardPage from "../pages/Dashboard/DashboardPage";
import {
  ANALYSIS_SUGGESTIONS,
  TOOL_LABELS,
  TRACKED_STOCKS,
} from "../lib/constants";
import type { AskResponse, Message, ToolStep } from "../lib/api-client";

let msgId = 0;
const uid = () => ++msgId;

export default function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [steps, setSteps] = useState<ToolStep[]>([]);
  const [streamingAnswer, setStreamingAnswer] = useState("");
  const [streamingSymbol, setStreamingSymbol] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const pendingTimeoutsRef = useRef<Set<number>>(new Set());

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, loading]);

  // Abort any in-flight request and clear any pending step timeouts when
  // the component unmounts, so a stale request can't keep writing into
  // state after the tree is gone.
  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort();
      pendingTimeoutsRef.current.forEach((id) => window.clearTimeout(id));
      pendingTimeoutsRef.current.clear();
    };
  }, []);

  const submit = useCallback(async (question: string) => {
    const q = question.trim();
    if (!q || loading) return;

    // Cancel any previous in-flight request (and its pending step-clear
    // timeouts) before starting a new one, so an older stream can't keep
    // writing into streamingAnswer/messages after a newer request starts.
    abortControllerRef.current?.abort();
    pendingTimeoutsRef.current.forEach((id) => window.clearTimeout(id));
    pendingTimeoutsRef.current.clear();

    const controller = new AbortController();
    abortControllerRef.current = controller;

    const userMsg: Message = {
      id: uid(),
      type: "user",
      content: q,
    };

    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);
    setSteps([]);
    setStreamingAnswer("");
    setStreamingSymbol(null);

    const addStep = (tool: string) => {
      const label = TOOL_LABELS[tool] ?? tool;

      setSteps((prev) => {
        if (
          prev.some(
            (step) => step.tool === tool && step.status === "running",
          )
        ) {
          return prev;
        }

        return [
          ...prev,
          {
            id: uid(),
            tool,
            label,
            status: "running",
          },
        ];
      });
    };

    const completeStep = (tool: string) => {
      setSteps((prev) =>
        prev.map((step) =>
          step.tool === tool && step.status === "running"
            ? { ...step, status: "done" }
            : step,
        ),
      );

      const timeoutId = window.setTimeout(() => {
        pendingTimeoutsRef.current.delete(timeoutId);
        setSteps((prev) =>
          prev.filter(
            (step) => !(step.tool === tool && step.status === "done"),
          ),
        );
      }, 250);

      pendingTimeoutsRef.current.add(timeoutId);
    };

    const runStream = async () => {
      await streamAskQuestion(
        q,
        {
          onToolCall: (tool, status) => {
            if (status === "calling") addStep(tool);
            if (status === "done") completeStep(tool);
          },
          onToken: (content) => {
            setStreamingAnswer((prev) =>
              prev ? `${prev} ${content}` : content,
            );
          },
          onMetadata: setStreamingSymbol,
          onResult: (normalized: AskResponse) => {
            setMessages((prev) => [
              ...prev,
              {
                id: uid(),
                type: "assistant",
                answer: normalized.answer,
                symbol: normalized.symbol,
                event_type: normalized.event_type,
                event_date: normalized.event_date,
                magnitude: normalized.magnitude,
                sources: normalized.sources,
              },
            ]);
          },
        },
        controller.signal,
      );
    };

    try {
      await runStream();
    } catch (streamError) {
      // An abort here means this request was superseded by a newer one (or
      // the component unmounted) — the newer request owns state updates
      // now, so don't fall back and don't touch loading/steps below.
      if (
        streamError instanceof DOMException &&
        streamError.name === "AbortError"
      ) {
        return;
      }

      try {
        const data = await askQuestion(q, controller.signal);

        const assistantMsg: Message = {
          id: uid(),
          type: "assistant",
          answer: data.answer,
          symbol: data.symbol,
          event_type: data.event_type,
          event_date: data.event_date,
          magnitude: data.magnitude,
          sources: data.sources,
        };

        setMessages((prev) => [...prev, assistantMsg]);
      } catch (fallbackError) {
        const message =
          fallbackError instanceof Error
            ? fallbackError.message
            : "Request failed";

        setMessages((prev) => [
          ...prev,
          {
            id: uid(),
            type: "assistant",
            error: message,
            answer: null,
            sources: [],
          },
        ]);
      }
    } finally {
      // Only this request's own controller may reset loading/steps/streaming
      // state — if it's been replaced, a newer submit() already owns that
      // state and this stale request must not touch it.
      if (abortControllerRef.current === controller) {
        setLoading(false);
        setStreamingAnswer("");
        setSteps([]);
      }
    }
  }, [loading]);

  // Stable reference: keeps RightRail's props unchanged across App re-renders
  // (input keystrokes, streaming tokens) so its React.memo can skip
  // re-rendering the rail's panels.
  const handleEventSelect = useCallback(
    (question: string) => void submit(question),
    [submit],
  );

  const handleSuggestion = useCallback(
    (suggestion: string) => void submit(suggestion),
    [submit],
  );

  const handleStock = useCallback(
    (symbol: string) => void submit(`Why did ${symbol} move recently?`),
    [submit],
  );

  // Clears the conversation back to the empty state instead of a real
  // `window.location.reload()` — a full reload would drop the in-flight
  // AbortController ungracefully and re-mount the whole app. This cancels
  // any in-flight request/pending timeouts the same way unmount does, then
  // resets every piece of state `submit()` touches.
  const handleReset = useCallback(() => {
    abortControllerRef.current?.abort();
    pendingTimeoutsRef.current.forEach((id) => window.clearTimeout(id));
    pendingTimeoutsRef.current.clear();

    setMessages([]);
    setLoading(false);
    setSteps([]);
    setStreamingAnswer("");
    setStreamingSymbol(null);
  }, []);

  return (
    <AppLayout
      onEventSelect={handleEventSelect}
      onLogoClick={handleReset}
      trackedStocksCount={TRACKED_STOCKS.length}
    >
      <DashboardPage
        messages={messages}
        loading={loading}
        steps={steps}
        streamingAnswer={streamingAnswer}
        streamingSymbol={streamingSymbol}
        onSubmit={submit}
        onSuggestion={handleSuggestion}
        onStock={handleStock}
        bottomRef={bottomRef}
        suggestions={ANALYSIS_SUGGESTIONS}
        trackedStocks={TRACKED_STOCKS}
      />
    </AppLayout>
  );
}