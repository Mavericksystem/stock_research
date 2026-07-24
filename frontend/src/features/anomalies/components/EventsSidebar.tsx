import { useCallback, useEffect, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import {
  STOCKS,
  fetchEventsForSymbol,
  type AnomalyEvent,
} from "../api";

interface EventsSidebarProps {
  open: boolean;
  onToggle: () => void;
  onEventSelect: (question: string) => void;
}

interface SkeletonCardProps {
  index: number;
}

function SkeletonCard({ index }: SkeletonCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: index * 0.04, duration: 0.2 }}
      aria-hidden="true"
      className="rounded-xl border border-[#3d3833] bg-[#2a2723] p-3"
    >
      <div className="mb-2 flex items-center justify-between">
        <div className="h-3 w-9 animate-pulse rounded bg-white/[0.06]" />
        <div className="h-[18px] w-12 animate-pulse rounded bg-white/[0.06]" />
      </div>
      <div className="h-2.5 w-[70px] animate-pulse rounded bg-white/[0.04]" />
    </motion.div>
  );
}

interface EventCardProps {
  event: AnomalyEvent;
  onClick: () => void;
  index: number;
}

function EventCard({ event, onClick, index }: EventCardProps) {
  const isSpike = (event.event_type ?? "").includes("SPIKE");
  const magnitude =
    event.magnitude != null
      ? `${isSpike ? "+" : ""}${parseFloat(String(event.magnitude)).toFixed(2)}%`
      : null;
  const zscore =
    event.normalized_score != null
      ? `z=${parseFloat(String(event.normalized_score)).toFixed(1)}`
      : null;

  return (
    <motion.button
      type="button"
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: Math.min(index * 0.025, 0.2), duration: 0.2 }}
      whileHover={{ x: 2, borderColor: "rgba(255,255,255,0.16)" }}
      whileTap={{ scale: 0.985 }}
      onClick={onClick}
      title={`Why did ${event.symbol} ${isSpike ? "spike" : "drop"} on ${event.start_date}?`}
      className="block w-full rounded-xl border border-[#3d3833] bg-[#2a2723] p-3 text-left transition-colors duration-200 hover:bg-[#322f2b] focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--amber)]/60"
    >
      <div className="mb-1 flex items-center justify-between gap-1.5">
        <span className="font-mono text-xs font-medium tracking-[0.02em] text-white">
          {event.symbol}
        </span>
        <span
          className={`shrink-0 rounded border px-1.5 py-0.5 font-mono text-[10px] font-medium tracking-[0.02em] ${
            isSpike
              ? "border-emerald-500/20 bg-emerald-500/[0.12] text-[var(--spike)]"
              : "border-red-500/20 bg-red-500/[0.12] text-[var(--drop)]"
          }`}
        >
          {isSpike ? "▲" : "▼"}
          {magnitude ? ` ${magnitude}` : ""}
        </span>
      </div>

      <div className="flex items-center justify-between gap-2 text-[8px] text-white/80">
        <span className="font-mono">{event.start_date}</span>
        {zscore && <span className="font-mono">{zscore}</span>}
      </div>
    </motion.button>
  );
}

export default function EventsSidebar({
  open,
  onToggle,
  onEventSelect,
}: EventsSidebarProps) {
  const [events, setEvents] = useState<AnomalyEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  const [edgeHovered, setEdgeHovered] = useState(false);
  const [panelHovered, setPanelHovered] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const reduceMotion = useReducedMotion();

  const desktopOpen = edgeHovered || panelHovered;
  const drawerOpen = open || desktopOpen;
  const drawerWidth = "min(280px, 82vw)";

  useEffect(() => {
    const mediaQuery = window.matchMedia("(max-width: 768px)");
    const updateMobile = () => setIsMobile(mediaQuery.matches);

    updateMobile();
    mediaQuery.addEventListener("change", updateMobile);
    return () => mediaQuery.removeEventListener("change", updateMobile);
  }, []);

  const loadEvents = useCallback(() => {
    setLoading(true);

    void Promise.allSettled(STOCKS.map(fetchEventsForSymbol)).then(
      (results) => {
        const all = results
          .filter(
            (result): result is PromiseFulfilledResult<AnomalyEvent[]> =>
              result.status === "fulfilled",
          )
          .flatMap((result) => result.value)
          .filter((event) => event?.start_date)
          .sort(
            (a, b) =>
              new Date(b.start_date ?? 0).getTime() -
              new Date(a.start_date ?? 0).getTime(),
          )
          .slice(0, 25);

        setEvents(all);
        setLoading(false);
        setLastRefresh(new Date());
      },
    );
  }, []);

  useEffect(() => {
    loadEvents();
  }, [loadEvents]);

  const handleSelect = (event: AnomalyEvent) => {
    const direction = (event.event_type ?? "").includes("SPIKE")
      ? "spike"
      : "drop";

    onEventSelect(
      `Why did ${event.symbol} ${direction} on ${event.start_date}?`,
    );

    if (window.matchMedia("(max-width: 768px)").matches && open) {
      onToggle();
    }
  };

  return (
    <div className="pointer-events-none absolute inset-0 z-[1100] overflow-visible">
      <div
        aria-hidden="true"
        className="pointer-events-auto absolute inset-y-0 left-0 hidden w-5 md:block"
        onMouseEnter={() => setEdgeHovered(true)}
        onMouseLeave={() => setEdgeHovered(false)}
      />

      <motion.div
        aria-hidden="true"
        animate={{
          width: desktopOpen ? 4 : 3,
          opacity: desktopOpen ? 0.5 : 0.25,
        }}
        transition={{ duration: 0.18 }}
        className="pointer-events-none absolute left-0 top-1/2 hidden h-11 -translate-y-1/2 rounded-r bg-white md:block"
      />

      <motion.button
        type="button"
        aria-label={open ? "Close anomalies" : "Open anomalies"}
        aria-expanded={open}
        onClick={onToggle}
        animate={{ x: open ? drawerWidth : 0 }}
        transition={
          reduceMotion
            ? { duration: 0 }
            : { type: "spring", stiffness: 430, damping: 34, mass: 0.7 }
        }
        className="pointer-events-auto absolute left-0 top-1/2 z-[1201] flex h-14 w-5 -translate-y-1/2 items-center justify-center rounded-r-md border border-l-0 border-white/[0.06] bg-white/[0.07] md:hidden"
      >
        <motion.span
          animate={{ height: open ? 34 : 28 }}
          className="block w-[3px] rounded-full bg-white/35"
        />
      </motion.button>

      <AnimatePresence>
        {open && (
          <motion.button
            type="button"
            aria-label="Close anomalies"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={onToggle}
            className="pointer-events-auto absolute inset-0 z-[1000] bg-black/45 md:hidden"
          />
        )}
      </AnimatePresence>

      <AnimatePresence initial={false}>
        {drawerOpen && (
          <motion.aside
            key="anomalies-drawer"
            initial={isMobile ? { opacity: 0 } : { x: "-100%", opacity: 0 }}
            animate={isMobile ? { opacity: 1 } : { x: 0, opacity: 1 }}
            exit={isMobile ? { opacity: 0 } : { x: "-100%", opacity: 0 }}
            transition={
              reduceMotion
                ? { duration: 0 }
                : isMobile
                  ? { duration: 0.18 }
                  : {
                      type: "spring",
                      stiffness: 360,
                      damping: 36,
                      mass: 0.8,
                    }
            }
            onMouseEnter={() => setPanelHovered(true)}
            onMouseLeave={() => setPanelHovered(false)}
            aria-label="Recent market anomalies"
            className="pointer-events-auto absolute inset-y-0 left-0 z-[1101] flex h-full w-[min(280px,82vw)] min-h-0 flex-col overflow-hidden border-r border-[#3d3833] bg-[#24211d] shadow-[8px_0_30px_rgba(0,0,0,0.18)] backdrop-blur-xl md:h-auto md:w-[220px]"
          >
            <div className="flex shrink-0 items-center justify-between border-b border-white/[0.05] px-3.5 pb-2.5 pt-4">
              <span className="text-[13px] font-bold tracking-[0.08em] text-white">
                ANOMALIES
              </span>

              <motion.button
                type="button"
                whileHover={{ scale: 1.08 }}
                whileTap={{ scale: 0.92 }}
                onClick={loadEvents}
                disabled={loading}
                aria-label="Refresh anomalies"
                title="Refresh"
                className="flex items-center rounded p-[3px] text-white/35 transition-colors hover:text-white/60 disabled:cursor-default disabled:opacity-50"
              >
                <motion.svg
                  width="13"
                  height="13"
                  viewBox="0 0 13 13"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  animate={loading ? { rotate: 360 } : { rotate: 0 }}
                  transition={
                    loading
                      ? { duration: 0.8, repeat: Infinity, ease: "linear" }
                      : { duration: 0.15 }
                  }
                >
                  <path d="M11.5 2A5.5 5.5 0 0 0 1 6.5" />
                  <path d="M1.5 11A5.5 5.5 0 0 0 12 6.5" />
                  <polyline points="11.5,2 11.5,5.5 8,5.5" />
                  <polyline points="1.5,11 1.5,7.5 5,7.5" />
                </motion.svg>
              </motion.button>
            </div>

            <div className="h-0 min-h-0 flex-1 overflow-y-auto overflow-x-hidden overscroll-contain p-2 scrollbar-thin scrollbar-thumb-white/10 [touch-action:pan-y] [-webkit-overflow-scrolling:touch] md:h-auto">
              {loading ? (
                <div className="space-y-2">
                  {Array.from({ length: 6 }).map((_, index) => (
                    <SkeletonCard key={index} index={index} />
                  ))}
                </div>
              ) : events.length === 0 ? (
                <div className="px-2.5 py-6 text-center font-mono text-[11px] text-white/25">
                  No anomalies in range
                </div>
              ) : (
                <div className="space-y-2">
                  {events.map((event, index) => (
                    <EventCard
                      key={`${event.symbol}-${event.start_date}-${index}`}
                      event={event}
                      index={index}
                      onClick={() => handleSelect(event)}
                    />
                  ))}
                </div>
              )}
            </div>

            {lastRefresh && (
              <div className="shrink-0 border-t border-white/[0.04] px-3.5 pb-3 pt-2 font-mono text-[10px] text-white/25">
                Updated{" "}
                {lastRefresh.toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </div>
            )}
          </motion.aside>
        )}
      </AnimatePresence>
    </div>
  );
}
