import { z } from "zod";

/* ---------------------------------------------------------------------- */
/* /api/v1/ask + /api/v1/ask/stream                                       */
/* ---------------------------------------------------------------------- */

export const SourceSchema = z.object({
  title: z.string().nullable().default(null),
  source: z.string().nullable().default(null),
  url: z.string().nullable().default(null),
  relevance_score: z.number().nullable().default(null),
});

/**
 * Final, render-ready shape. Validated right before it reaches the UI so a
 * backend shape drift (e.g. `magnitude` sent as a numeric string) fails
 * safe instead of throwing inside a `.toFixed()` call at render time.
 */
export const AskResponseSchema = z.object({
  answer: z.string(),
  symbol: z.string().nullable(),
  event_type: z.string().nullable(),
  event_date: z.string().nullable(),
  magnitude: z.number().nullable(),
  sources: z.array(SourceSchema),
});

/**
 * Raw backend payload — loose on purpose. The backend's `explanation` shape
 * has changed before (see docs/05-current-state.md's citations TODO), so
 * this only asserts the handful of fields normalizeAskResponse() actually
 * reads, and passes everything else through untouched.
 */
export const RawAskPayloadSchema = z
  .object({
    symbol: z.string().nullable().optional(),
    explanation: z
      .object({
        explanation: z.union([z.string(), z.array(z.string())]).optional(),
        primary_cause: z.string().optional(),
      })
      .optional(),
    event_type: z.string().nullable().optional(),
    event_date: z.string().nullable().optional(),
    magnitude: z.number().nullable().optional(),
    tool_calls_made: z
      .array(
        z.object({
          tool: z.string().optional(),
          result: z.unknown().optional(),
        }),
      )
      .optional(),
  })
  .passthrough();

/* ---------------------------------------------------------------------- */
/* SSE stream envelope (/api/v1/ask/stream)                               */
/* ---------------------------------------------------------------------- */

export const StreamEventSchema = z
  .object({
    type: z.enum(["tool_call", "token", "metadata", "result"]).optional(),
    status: z.enum(["calling", "done"]).optional(),
    tool: z.string().optional(),
    content: z.unknown().optional(),
    symbol: z.string().optional(),
    data: z.unknown().optional(),
  })
  .passthrough();

/* ---------------------------------------------------------------------- */
/* /api/v1/stocks/{symbol}/prices + /api/v1/stocks/stream                 */
/* ---------------------------------------------------------------------- */

export const RawPriceRowSchema = z.object({
  date: z.string(),
  close: z.number(),
  adj_close: z.number().optional(),
});

export const PriceResponseSchema = z.object({
  data: z
    .object({
      prices: z.array(RawPriceRowSchema).optional(),
    })
    .optional(),
});

export const LiveSnapshotSchema = z.object({
  prices: z
    .record(z.object({ price: z.number(), t: z.number().optional() }))
    .optional(),
  connected: z.boolean().optional(),
});

/* ---------------------------------------------------------------------- */
/* /api/v1/news/latest                                                    */
/* ---------------------------------------------------------------------- */

export const NewsItemSchema = z.object({
  id: z.number(),
  symbol: z.string().nullable().optional(),
  title: z.string().nullable().optional(),
  content: z.string().nullable(),
  source: z.string(),
  url: z.string(),
  published_at: z.string(),
});

export const NewsListResponseSchema = z.object({
  data: z.array(NewsItemSchema).optional(),
});

/* ---------------------------------------------------------------------- */
/* /api/v1/stocks/{symbol}/events                                         */
/* ---------------------------------------------------------------------- */

/**
 * Raw per-symbol event row from GET /api/v1/stocks/{symbol}/events.
 *
 * Matches `backend/api/schemas.py`'s `EventResponse` exactly: that model
 * has NO `symbol` field at all (the endpoint is already scoped to one
 * symbol in the URL path), so `symbol` here must stay optional —
 * `fetchEventsForSymbol` in `features/anomalies/api.ts` attaches the real
 * symbol itself after parsing. Requiring it here previously caused every
 * event to fail validation and silently return `[]`.
 */
export const AnomalyEventSchema = z
  .object({
    symbol: z.string().optional(),
    event_type: z.string().nullable().optional(),
    magnitude: z.union([z.number(), z.string()]).nullable().optional(),
    normalized_score: z.union([z.number(), z.string()]).nullable().optional(),
    start_date: z.string().nullable().optional(),
  })
  .passthrough();

export const AnomalyEventsResponseSchema = z.object({
  data: z.array(AnomalyEventSchema).optional(),
});
