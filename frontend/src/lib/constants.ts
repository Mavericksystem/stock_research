export const TRACKED_STOCKS = [
  "AAPL",
  "MSFT",
  "NVDA",
  "GOOGL",
  "AMZN",
  "META",
  "TSLA",
  "JPM",
  "V",
  "WMT",
] as const;

export const ANALYSIS_SUGGESTIONS = [
  "Why did NVDA drop recently?",
  "What caused Apple's last spike?",
  "Explain Tesla's latest move",
] as const;

export const TOOL_LABELS: Record<string, string> = {
  get_event_details: "Fetching event details",
  get_technical_state: "Reading technical state",
  get_news_context: "Retrieving news context",
  get_price_history: "Loading price history",
};

export type TrackedStock = (typeof TRACKED_STOCKS)[number];
