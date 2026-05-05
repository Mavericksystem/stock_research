import os
import sys
from datetime import datetime, timedelta, date, timezone
from typing import Any, cast

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import httpx
from dotenv import load_dotenv
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy import func
from backend.ingestion.embeddings import MODEL_NAME, embed_texts, embed_text, cosine_similarity
from backend.db.connection import engine
from backend.db.models import News, Event, EventNewsLink

load_dotenv()
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def fetch_finnhub_news(symbol: str, from_date: date, to_date: date) -> list[dict[str, Any]]:
    if not FINNHUB_API_KEY:
        raise ValueError("FINNHUB_API_KEY not set")
    url = "https://finnhub.io/api/v1/company-news"
    params = {
        "symbol": symbol,
        "from": from_date.isoformat(),
        "to": to_date.isoformat(),
        "token": FINNHUB_API_KEY,
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.get(url, params=params)
        r.raise_for_status()
        data = r.json()
        if not isinstance(data, list):
            return []
        return cast(list[dict[str, Any]], data)

def transform_finnhub_news(rows: list[dict[str, Any]], symbol: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in rows:
        ts = item.get("datetime")
        published_at = None
        if ts:
            published_at = datetime.fromtimestamp(int(ts), tz=timezone.utc).replace(tzinfo=None)

        transformed: dict[str, Any] = {
            "symbol": symbol,
            "title": item.get("headline"),
            "content": item.get("summary"),
            "source": item.get("source") or "finnhub",
            "url": item.get("url"),
            "published_at": published_at,
        }
        out.append(transformed)

    return [x for x in out if x.get("url") and x.get("published_at")]


SYMBOL_TO_NAME = {
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "NVDA": "NVIDIA",
    "GOOGL": "Google",
    "AMZN": "Amazon",
    "META": "Meta",
    "TSLA": "Tesla",
    "JPM": "JP Morgan",
    "V": "Visa",
    "WMT": "Walmart",
}

GENERIC_TITLE_PHRASES = [
    "what to watch",
    "what to expect",
    "futures",
    "earnings season",
    "earnings wave",
    "week ahead",
    "take the spotlight",
    "stock market",
    "dow jones futures",
    "mag 7",
]

OPINION_TITLE_PHRASES = [
    "buy",
    "buy now",
    "good stock",
    "best stock",
    "top stock",
    "top stocks",
    "should you",
    "investors should",
    "for beginner",
    "beginner",
    "portfolio",
    "foundational asset",
    "made me buy",
]

CAUSAL_TITLE_PHRASES = [
    "why ",
    "popped",
    "plung",
    "tumbled",
    "dropped",
    "surged",
    "gains after",
    "after earnings",
    "ahead of earnings",
    "price target",
    "downgrade",
    "upgrade",
]

# ---------------------------------------------------------------------------
# Fix 8: Asymmetric time score — pre-event is more likely causal than
# post-event. Same-day is top regardless of direction. Post-event commentary
# tapers faster than pre-event news.
# ---------------------------------------------------------------------------
def time_score_refined(event_date: date, published_at: datetime) -> float:
    """Directional day-based recency score.

    delta < 0  → article published BEFORE event (more likely causal driver)
    delta == 0 → same day
    delta > 0  → article published AFTER event (reaction / analysis)

    Pre-event scores taper slowly; post-event tapers faster.
    """
    delta = (published_at.date() - event_date).days  # negative = before event

    if delta == 0:
        return 1.0

    if delta < 0:
        # Pre-event: 1 day before is nearly as good as same-day
        days_before = abs(delta)
        if days_before == 1:
            return 0.85
        if days_before == 2:
            return 0.60
        return 0.20

    # Post-event: reaction pieces are less causally relevant, taper quickly
    if delta == 1:
        return 0.45
    if delta == 2:
        return 0.15
    return 0.0


# ---------------------------------------------------------------------------
# Fix 3: Entity score — ticker (WMT) is a stronger signal than company name
# (Walmart) because the company name appears in almost every headline for
# large-cap stocks. Reduce the company-name-only score from 1.0 → 0.55 to
# restore discriminating power.
# ---------------------------------------------------------------------------
def entity_score_refined(title: str | None, symbol: str, company_name: str) -> float:
    t = (title or "").lower()
    sym = symbol.lower()
    nm = company_name.lower()

    if sym in t:
        # Explicit ticker mention → high confidence this is about the stock
        return 1.0
    if nm and nm in t:
        # Company name in title — useful but near-constant for big brands,
        # so we assign a reduced score instead of the old 1.0
        return 0.55
    return 0.20


# ---------------------------------------------------------------------------
# Fix 4 / Fix 6: Headline signal with a wider effective range.
# Returns a float where:
#   causal-proxy headlines   → ~1.0
#   neutral                  → ~0.5
#   opinion / listicle       → ~0.0
#
# The weight assigned to this in the final formula has been raised (0.25)
# so the 1.0-point spread now moves the final score by 0.25 instead of 0.10.
# ---------------------------------------------------------------------------
def headline_signal_score(title: str | None) -> float:
    t = (title or "").lower()

    has_causal = any(p in t for p in CAUSAL_TITLE_PHRASES)
    has_opinion = any(p in t for p in OPINION_TITLE_PHRASES)
    has_generic = any(p in t for p in GENERIC_TITLE_PHRASES)

    if has_causal and has_opinion:
        # "Why Apple's Buy Rating Was Upgraded" — causal wins but softened
        return 0.70
    if has_causal:
        return 1.0
    if has_opinion:
        # Previously 0.0 with weight 0.1 → only –0.05 effect.
        # Now 0.0 with weight 0.25 → –0.125 effect AND eligible for cap below.
        return 0.0
    if has_generic:
        return 0.25
    return 0.50


def generic_title_factor(title: str | None) -> float:
    t = (title or "").lower()
    hits = sum(1 for p in GENERIC_TITLE_PHRASES if p in t)
    if hits <= 0:
        return 1.0
    if hits == 1:
        return 0.88
    return 0.80


def opinion_title_factor(title: str | None) -> float:
    t = (title or "").lower()
    hits = sum(1 for p in OPINION_TITLE_PHRASES if p in t)
    if hits <= 0:
        return 1.0
    if hits == 1:
        return 0.70
    return 0.62


def causal_title_boost(title: str | None) -> float:
    t = (title or "").lower()
    hits = sum(1 for p in CAUSAL_TITLE_PHRASES if p in t)
    if hits <= 0:
        return 1.0
    if hits == 1:
        return 1.10
    return 1.15


def entity_mention_factor(title: str | None, content: str | None, symbol: str, name: str) -> float:
    t = (title or "").lower()
    c = (content or "").lower()
    sym = symbol.lower()
    nm = name.lower()
    mentioned = (sym in t) or (sym in c) or (nm in t) or (nm in c)
    return 1.0 if mentioned else 0.78


# ---------------------------------------------------------------------------
# Fix 1: build_event_text — rewritten as a coherent causal question.
#
# Embedding models are trained on natural language. A coherent interrogative
# sentence ("Why did Walmart stock drop 5%? What news caused the selloff?")
# embeds into a much tighter, more specific vector than a keyword bag
# ("Walmart WMT sharp sudden unusual stock drop selloff 5 percent move").
# The sharper vector makes cosine similarity more discriminating, which
# in turn allows the 0.45 semantic weight to do real work instead of
# giving a uniform high score to all Walmart headlines.
# ---------------------------------------------------------------------------
def build_event_text(event: Event) -> str:
    symbol = cast(str, event.symbol)
    name = SYMBOL_TO_NAME.get(symbol, symbol)

    ctx = cast(dict[str, Any] | None, event.context) or {}
    rsi = ctx.get("rsi")
    volatility = ctx.get("volatility")
    above_sma_20 = ctx.get("above_sma_20")
    z_score = ctx.get("z_score")
    magnitude = getattr(event, "magnitude", None)

    et = (event.event_type or "").upper()
    if "DROP" in et:
        direction_verb = "drop"
        direction_noun = "decline"
        market_word = "selloff"
    elif "SPIKE" in et:
        direction_verb = "surge"
        direction_noun = "rally"
        market_word = "spike"
    else:
        direction_verb = "move"
        direction_noun = "price move"
        market_word = "move"

    # Build magnitude phrase, e.g. "5%" or "sharply"
    pct_phrase = "sharply"
    if isinstance(magnitude, (int, float)):
        pct = abs(float(magnitude)) * 100.0
        if pct >= 1.0:
            pct_phrase = f"{pct:.0f}%"

    # Enrich with context clues that help semantic matching
    context_clauses: list[str] = []

    if isinstance(rsi, (int, float)):
        if rsi < 30:
            context_clauses.append("RSI oversold conditions")
        elif rsi > 70:
            context_clauses.append("RSI overbought conditions")

    if isinstance(volatility, (int, float)) and volatility >= 0.03:
        context_clauses.append("high volatility environment")

    if isinstance(z_score, (int, float)):
        z = abs(float(z_score))
        if z >= 3.0:
            context_clauses.append("extreme anomalous volume")
        elif z >= 2.0:
            context_clauses.append("anomalous trading activity")

    if above_sma_20 is True:
        context_clauses.append("stock trading above 20-day moving average")
    elif above_sma_20 is False:
        context_clauses.append("stock trading below 20-day moving average")

    today = datetime.now(timezone.utc).date()
    event_day = cast(date, event.start_date)
    recency = "today" if event_day == today else f"on {event_day.isoformat()}"

    # Core causal question — what a financial analyst would search for
    base = (
        f"Why did {name} ({symbol}) stock {direction_verb} {pct_phrase} {recency}? "
        f"What news catalyst caused the {name} {direction_noun}? "
        f"{name} {symbol} {market_word} reason announcement earnings guidance."
    )

    if context_clauses:
        base += " " + "; ".join(context_clauses) + "."

    return base


async def upsert_news(news_rows: list[dict[str, Any]]) -> None:
    if not news_rows:
        return

    urls = [cast(str, r.get("url")) for r in news_rows if r.get("url")]
    if not urls:
        return

    async with SessionLocal() as session:
        existing_q = select(News.url).where(News.url.in_(urls), News.embedding.isnot(None))
        existing_res = await session.execute(existing_q)
        embedded_urls = set(existing_res.scalars().all())

        texts_to_embed: list[str] = []
        row_indices: list[int] = []

        for i, row in enumerate(news_rows):
            url = row.get("url")
            if not url or url in embedded_urls:
                continue

            title = cast(str | None, row.get("title"))
            content = cast(str | None, row.get("content"))
            text = " ".join([x for x in [title, content] if x]).strip()
            if not text:
                continue

            texts_to_embed.append(text)
            row_indices.append(i)

        BATCH = 20
        for start in range(0, len(texts_to_embed), BATCH):
            batch_texts = texts_to_embed[start : start + BATCH]
            batch_vecs = embed_texts(batch_texts)
            now = datetime.now(timezone.utc)

            for j, vec in enumerate(batch_vecs):
                row_i = row_indices[start + j]
                news_rows[row_i]["embedding"] = vec
                news_rows[row_i]["embedding_model"] = MODEL_NAME
                news_rows[row_i]["embedding_created_at"] = now

        for row in news_rows:
            row.setdefault("embedding", None)
            row.setdefault("embedding_model", None)
            row.setdefault("embedding_created_at", None)

        stmt = insert(News).values(news_rows)
        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=["url"],
            set_={
                "symbol": stmt.excluded.symbol,
                "title": stmt.excluded.title,
                "content": stmt.excluded.content,
                "source": stmt.excluded.source,
                "published_at": stmt.excluded.published_at,
                "embedding": func.coalesce(News.embedding, stmt.excluded.embedding),
                "embedding_model": func.coalesce(News.embedding_model, stmt.excluded.embedding_model),
                "embedding_created_at": func.coalesce(News.embedding_created_at, stmt.excluded.embedding_created_at),
            },
        )

        await session.execute(upsert_stmt)
        await session.commit()


STRONG_KEYWORDS = [
    "earnings", "revenue", "profit", "guidance",
    "downgrade", "upgrade", "rating",
    "acquisition", "merger",
    "lawsuit", "sec", "investigation",
]

WEAK_KEYWORDS = [
    "ai", "stock", "market", "investment",
    "crypto", "portfolio"
]

NEGATIVE_KEYWORDS = [
    "crypto", "bitcoin", "etf", "macro", "inflation"
]


def time_score(event_date: date, published_at: datetime) -> float:
    days = abs((published_at.date() - event_date).days)
    if days == 0:
        return 1.0
    elif days == 1:
        return 0.7
    elif days == 2:
        return 0.4
    else:
        return 0.0


def title_score(title: str | None) -> float:
    t = (title or "").lower()
    score = 0.0
    for w in STRONG_KEYWORDS:
        if w in t:
            score += 1.0
    for w in WEAK_KEYWORDS:
        if w in t:
            score += 0.2
    return min(score, 2.0)


def entity_score(title: str | None, symbol: str) -> float:
    t = (title or "").lower()
    if symbol.lower() in t:
        return 1.0
    return 0.3


def penalty(title: str | None) -> float:
    t = (title or "").lower()
    for w in NEGATIVE_KEYWORDS:
        if w in t:
            return -0.5
    return 0.0


def relevance_score_v2(event_dt: date, published_at: datetime, title: str | None, symbol: str) -> float:
    t_score = time_score(event_dt, published_at)
    title_s = title_score(title)
    entity_s = entity_score(title, symbol)
    p = penalty(title)

    final = (t_score * 0.5) + (title_s * 0.3) + (entity_s * 0.2) + p
    return float(round(final, 4))


# ---------------------------------------------------------------------------
# Fix 5: opinion cap threshold used in link_event_to_news.
# Articles classified as pure opinion/listicle (and not redeemed by a causal
# signal) are capped at this score regardless of semantic similarity.
# This avoids the hard-delete risk while still demoting noise strongly.
# ---------------------------------------------------------------------------
OPINION_SCORE_CAP = 0.35

# Guardrail: if the article doesn't mention the symbol/company in title or
# content, cap it (Finnhub company-news often includes adjacent-market items).
OFFTOPIC_SCORE_CAP = 0.40


async def link_event_to_news(event_id: int, symbol: str, window_days: int = 2, limit: int = 50) -> int:
    async with SessionLocal() as session:
        event = await session.get(Event, event_id)
        if not event:
            return 0

        center = cast(date, event.start_date)
        start = datetime.combine(center - timedelta(days=window_days), datetime.min.time())
        end = datetime.combine(center + timedelta(days=window_days), datetime.max.time())

        news_q = (
            select(News)
            .where(News.symbol == symbol, News.published_at >= start, News.published_at <= end)
            .order_by(News.published_at.desc())
            .limit(limit)
        )
        res = await session.execute(news_q)
        candidates = res.scalars().all()

        if not candidates:
            return 0

        # Step 1: candidate retrieval — keyword pre-filter
        scored: list[tuple[News, float]] = []
        for n in candidates:
            kw = relevance_score_v2(
                center,
                cast(datetime, n.published_at),
                cast(str | None, n.title),
                symbol,
            )
            scored.append((n, kw))

        scored.sort(key=lambda x: x[1], reverse=True)

        kw_floor = 0.6
        filtered = [(n, kw) for n, kw in scored if kw >= kw_floor]
        if len(filtered) >= 10:
            scored = filtered

        # Step 2: compute event embedding once per event
        # Fix 1 pays off here: the natural-language event text produces a
        # tighter, more specific embedding vector.
        event_vec: list[float] | None
        try:
            event_vec = embed_text(build_event_text(event))
        except Exception:
            event_vec = None

        # Step 2.5: ensure candidate news have embeddings
        if event_vec is not None:
            to_embed_news: list[News] = []
            to_embed_texts: list[str] = []
            for n, _kw in scored:
                if n.embedding is not None:
                    continue
                title = cast(str | None, n.title)
                content = cast(str | None, n.content)
                text = " ".join([x for x in [title, content] if x]).strip()
                if not text:
                    continue
                to_embed_news.append(n)
                to_embed_texts.append(text)

            if to_embed_texts:
                try:
                    vecs = embed_texts(to_embed_texts)
                    now = datetime.now(timezone.utc)
                    for n, vec in zip(to_embed_news, vecs):
                        n.embedding = vec
                        n.embedding_model = MODEL_NAME
                        n.embedding_created_at = now
                    await session.commit()
                except Exception:
                    await session.rollback()

        # Step 3: weighted ranking
        #
        # Weight changes from original → new:
        #   semantic:  0.60 → 0.45  (Fix 2: was amplifying broad similarity)
        #   time:      0.15 → 0.20  (Fix 8: asymmetric scoring now earns this)
        #   entity:    0.15 → 0.10  (Fix 3: near-constant for big brands, reduced)
        #   headline:  0.10 → 0.25  (Fix 4: strongest prior for causality, raised)
        #
        # Fix 5: After the weighted sum, apply OPINION_SCORE_CAP for articles
        # that headline_signal_score() classifies as pure opinion/listicle
        # (score == 0.0) and that have no causal signal to redeem them.
        # This avoids hard-deleting (which risks losing "editorial but still
        # summarises the catalyst" articles) while strongly demoting noise.
        #
        # Fix 5b: causal_title_boost() is now wired as a post-sum multiplier
        # (capped at 1.0 to avoid inflating beyond the normalised range).
        ranked: list[tuple[int, float, dict[str, float], str]] = []
        company_name = SYMBOL_TO_NAME.get(symbol, symbol)

        for n, kw in scored:
            kw_norm = min(1.0, float(kw) / 1.3)

            semantic = kw_norm
            if event_vec is not None and n.embedding is not None:
                try:
                    semantic = float(cosine_similarity(event_vec, cast(list[float], n.embedding)))
                except Exception:
                    semantic = kw_norm

            title_str = cast(str | None, n.title)
            tscore  = time_score_refined(center, cast(datetime, n.published_at))
            escore  = entity_score_refined(title_str, symbol, company_name)
            hscore  = headline_signal_score(title_str)

            # Weighted sum with rebalanced weights (Fixes 2, 3, 4)
            final_score = (
                (semantic * 0.45)
                + (tscore  * 0.20)
                + (escore  * 0.10)
                + (hscore  * 0.25)
            )

            # Fix 5b: apply causal_title_boost as a bounded multiplier.
            # Keeps boosts meaningful without letting them escape [0, 1].
            boost = causal_title_boost(title_str)
            if boost > 1.0:
                final_score = final_score * boost

            final_score = float(min(1.0, max(0.0, final_score)))

            mentioned = entity_mention_factor(
                title_str,
                cast(str | None, n.content),
                symbol,
                company_name,
            )
            if mentioned < 1.0:
                final_score = min(final_score, OFFTOPIC_SCORE_CAP)

            # Fix 6: opinion cap — demote pure listicle/opinion headlines that
            # carry no causal signal. A soft cap is used rather than a hard
            # filter so that an article containing both opinion language AND a
            # causal keyword (e.g. a "Buy" rec following an upgrade) can still
            # score above the floor via headline_signal_score returning 0.7.
            is_opinion = hscore == 0.0  # opinion/listicle with no causal redemption
            if is_opinion:
                final_score = min(final_score, OPINION_SCORE_CAP)

            components = {
                "semantic":  float(round(semantic, 6)),
                "time":      float(round(tscore,   6)),
                "entity":    float(round(escore,   6)),
                "headline":  float(round(hscore,   6)),
            }
            ranked.append((cast(int, n.id), float(round(final_score, 6)), components, cast(str, n.title or "")))

        ranked.sort(key=lambda x: x[1], reverse=True)
        top = ranked[:5]

        link_rows = [
            {"event_id": event_id, "news_id": nid, "relevance_score": score}
            for nid, score, _c, _t in top
        ]

        print(
            f"[link] event_id={event_id} symbol={symbol} candidates={len(candidates)} "
            f"reranked={len(scored)} top_scores={[s for _, s, _c, _t in top]}"
        )

        if os.getenv("DEBUG_RANKING") in {"1", "true", "TRUE", "yes", "YES"}:
            for nid, score, comp, title in top:
                print(
                    f"  - news_id={nid} score={score} "
                    f"semantic={comp['semantic']} time={comp['time']} "
                    f"entity={comp['entity']} headline={comp['headline']} "
                    f"title={title[:90]}"
                )

        stmt = insert(EventNewsLink).values(link_rows)
        stmt = stmt.on_conflict_do_update(
            constraint="uix_event_news_link",
            set_={"relevance_score": stmt.excluded.relevance_score},
        )

        await session.execute(stmt)
        await session.commit()
        return len(link_rows)


async def run_context_for_symbol(symbol: str, days_back: int = 7):
    to_dt = datetime.now(timezone.utc).date()
    from_dt = to_dt - timedelta(days=days_back)

    data = await fetch_finnhub_news(symbol, from_dt, to_dt)
    rows = transform_finnhub_news(data, symbol)
    await upsert_news(rows)

    async with SessionLocal() as session:
        ev_q = (
            select(Event)
            .where(Event.symbol == symbol, Event.resolved == False)
            .order_by(Event.start_date.desc())
            .limit(20)
        )
        res = await session.execute(ev_q)
        events = res.scalars().all()

    for e in events:
        await link_event_to_news(cast(int, e.id), symbol)


if __name__ == "__main__":
    import asyncio

    async def main():
        for sym in ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN",
                    "META", "TSLA", "JPM", "V", "WMT"]:
            await run_context_for_symbol(sym, days_back=10)

    asyncio.run(main())