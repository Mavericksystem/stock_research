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

def time_score_refined(event_date: date, published_at: datetime) -> float:
    """Directional day-based recency score.

    delta < 0  → article published BEFORE event (more likely causal)
    delta == 0 → same day
    delta > 0  → article published AFTER event (more likely reaction)
    """
    delta = (published_at.date() - event_date).days

    if delta == 0:
        return 1.0

    if delta < 0:
        days_before = abs(delta)
        if days_before == 1:
            return 0.85
        if days_before == 2:
            return 0.60
        return 0.20

    if delta == 1:
        return 0.45
    if delta == 2:
        return 0.15
    return 0.0

def entity_score_refined(title: str | None, symbol: str, company_name: str) -> float:
    t = (title or "").lower()
    sym = symbol.lower()
    nm = company_name.lower()

    if sym and sym in t:
        return 1.0
    if nm and nm in t:
        return 0.55
    return 0.20

def headline_signal_score(title: str | None) -> float:
    """Score headline intent: causal proxy > neutral > opinion/listicle.

    Returns a value in [0, 1] where:
    - 1.0 is strongly causal
    - 0.5 is neutral
    - 0.0 is opinion/listicle
    """
    t = (title or "").lower()

    has_causal = any(p in t for p in CAUSAL_TITLE_PHRASES)
    has_opinion = any(p in t for p in OPINION_TITLE_PHRASES)
    has_generic = any(p in t for p in GENERIC_TITLE_PHRASES)

    if has_causal and has_opinion:
        return 0.7
    if has_causal:
        return 1.0
    if has_opinion:
        return 0.0
    if has_generic:
        return 0.25
    return 0.5

def generic_title_factor(title: str | None) -> float:
    t = (title or "").lower()
    hits = sum(1 for p in GENERIC_TITLE_PHRASES if p in t)
    if hits <= 0:
        return 1.0
    if hits == 1:
        return 0.88
    return 0.80

def opinion_title_factor(title: str | None) -> float:
    """Penalize listicles/opinion/investing-advice headlines (not causal signals)."""
    t = (title or "").lower()
    hits = sum(1 for p in OPINION_TITLE_PHRASES if p in t)
    if hits <= 0:
        return 1.0
    if hits == 1:
        return 0.70
    return 0.62

def causal_title_boost(title: str | None) -> float:
    """Boost headlines that are often direct causal proxies ("why moved today", earnings, target cuts)."""
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

    pct_phrase = "sharply"
    if isinstance(magnitude, (int, float)):
        pct = abs(float(magnitude)) * 100.0
        if pct >= 1.0:
            pct_phrase = f"{pct:.0f}%"

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
            context_clauses.append("extreme anomalous trading activity")
        elif z >= 2.0:
            context_clauses.append("anomalous trading activity")

    if above_sma_20 is True:
        context_clauses.append("stock trading above 20-day moving average")
    elif above_sma_20 is False:
        context_clauses.append("stock trading below 20-day moving average")

    today = datetime.now(timezone.utc).date()
    event_day = cast(date, event.start_date)
    recency = "today" if event_day == today else f"on {event_day.isoformat()}"

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

        # Important for SQLAlchemy multi-row INSERT: ensure every row has an explicit
        # Python-side value for these columns (None if missing), otherwise the compiler
        # may generate internal boundparameters that pgvector's type cannot handle.
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


OPINION_SCORE_CAP = 0.35
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

        # Step 1: candidate retrieval (bounded window by time via SQL + `limit`)
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

        # Loose keyword floor (lets semantic layer work but avoids pure garbage).
        # If too few survive, fall back to top-N by keyword.
        kw_floor = 0.6
        filtered = [(n, kw) for n, kw in scored if kw >= kw_floor]
        if len(filtered) >= 10:
            scored = filtered

        # Step 2: compute event embedding once per event
        event_vec: list[float] | None
        try:
            event_vec = embed_text(build_event_text(event))
        except Exception:
            event_vec = None

        # Step 2.5: ensure candidate news have embeddings (so semantic ranking can apply)
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
                    # If embedding fails, keep keyword-only fallback.
                    await session.rollback()

        # Step 3: weighted ranking (semantic + time + entity + headline intent)
        # final_score = semantic*0.45 + time*0.20 + entity*0.10 + headline*0.25
        ranked: list[tuple[int, float, dict[str, float], str]] = []
        company_name = SYMBOL_TO_NAME.get(symbol, symbol)
        for n, kw in scored:
            kw_norm = min(1.0, float(kw) / 1.3)

            # Semantic score with fallback (never skip).
            semantic = kw_norm
            if event_vec is not None and n.embedding is not None:
                try:
                    semantic = float(cosine_similarity(event_vec, cast(list[float], n.embedding)))
                except Exception:
                    semantic = kw_norm

            title_str = cast(str | None, n.title)
            tscore = time_score_refined(center, cast(datetime, n.published_at))
            escore = entity_score_refined(title_str, symbol, company_name)
            hscore = headline_signal_score(title_str)

            final_score = (
                (semantic * 0.45)
                + (tscore * 0.20)
                + (escore * 0.10)
                + (hscore * 0.25)
            )

            boost = causal_title_boost(title_str)
            if boost > 1.0:
                final_score = final_score * boost

            final_score = float(min(1.0, max(0.0, final_score)))

            # Guardrail: Finnhub "company-news" frequently includes adjacent-market headlines.
            # If the article doesn't mention the symbol/company in title or content, cap it.
            mentioned = entity_mention_factor(
                title_str,
                cast(str | None, n.content),
                symbol,
                company_name,
            )
            if mentioned < 1.0:
                final_score = min(final_score, OFFTOPIC_SCORE_CAP)

            is_opinion = hscore == 0.0
            if is_opinion:
                final_score = min(final_score, OPINION_SCORE_CAP)

            components = {
                "semantic": float(round(semantic, 6)),
                "time": float(round(tscore, 6)),
                "entity": float(round(escore, 6)),
                "headline": float(round(hscore, 6)),
            }
            ranked.append((cast(int, n.id), float(round(final_score, 6)), components, cast(str, n.title or "")))

        ranked.sort(key=lambda x: x[1], reverse=True)
        top = ranked[:5]

        link_rows = [{"event_id": event_id, "news_id": nid, "relevance_score": score} for nid, score, _c, _t in top]

        print(
            f"[link] event_id={event_id} symbol={symbol} candidates={len(candidates)} reranked={len(scored)} "
            f"top_scores={[s for _, s, _c, _t in top]}"
        )

        if os.getenv("DEBUG_RANKING") in {"1", "true", "TRUE", "yes", "YES"}:
            for nid, score, comp, title in top:
                print(
                    f"  - news_id={nid} score={score} "
                    f"semantic={comp['semantic']} time={comp['time']} entity={comp['entity']} headline={comp['headline']} "
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