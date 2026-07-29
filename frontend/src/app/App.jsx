import { useState, useRef, useEffect, useCallback } from "react";
import { askQuestion, streamAskQuestion } from "../features/analysis/api";
import AppLayout from "../layouts/AppLayout";
import DashboardPage from "../pages/Dashboard/DashboardPage";
import { ANALYSIS_SUGGESTIONS, TOOL_LABELS, TRACKED_STOCKS } from "../lib/constants";

let msgId = 0;
const uid = () => ++msgId;

export default function App() {
  const [messages, setMessages] = useState([]);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [steps, setSteps] = useState([]);
  const [streamingAnswer, setStreamingAnswer] = useState("");
  const [streamingSymbol, setStreamingSymbol] = useState(null);
  const bottomRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`;
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
        if (prev.some((step) => step.tool === tool && step.status === "running")) {
          return prev;
        }

        return [...prev, { id: uid(), tool, label, status: "running" }];
      });
    };

    const completeStep = (tool) => {
      setSteps((prev) =>
        prev.map((step) => (step.tool === tool && step.status === "running"
          ? { ...step, status: "done" }
          : step))
      );

      setTimeout(() => {
        setSteps((prev) => prev.filter((step) => !(step.tool === tool && step.status === "done")));
      }, 250);
    };

    const runStream = async () => {
      await streamAskQuestion(q, {
        onToolCall: (tool, status) => {
          if (status === "calling") addStep(tool);
          if (status === "done") completeStep(tool);
        },
        onToken: (content) => {
          setStreamingAnswer((prev) => (prev ? `${prev} ${content}` : content));
        },
        onMetadata: setStreamingSymbol,
        onResult: (normalized) => {
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
              sources: normalized.sources ?? [],
            },
          ]);
        },
      });
    };

    try {
      await runStream();
    } catch (error) {
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

  const handleKey = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      submit(input);
    }
  };

  return (
    <AppLayout
      sidebarOpen={sidebarOpen}
      onToggleSidebar={() => setSidebarOpen((value) => !value)}
      onEventSelect={(question) => submit(question)}
      trackedStocksCount={TRACKED_STOCKS.length}
    >
      <DashboardPage
        messages={messages}
        loading={loading}
        steps={steps}
        streamingAnswer={streamingAnswer}
        streamingSymbol={streamingSymbol}
        input={input}
        onInputChange={setInput}
        onKeyDown={handleKey}
        onSubmit={() => submit(input)}
        onSuggestion={(suggestion) => submit(suggestion)}
        onStock={(symbol) => submit(`Why did ${symbol} move recently?`)}
        bottomRef={bottomRef}
        textareaRef={textareaRef}
        suggestions={ANALYSIS_SUGGESTIONS}
        trackedStocks={TRACKED_STOCKS}
      />
    </AppLayout>
  );
}