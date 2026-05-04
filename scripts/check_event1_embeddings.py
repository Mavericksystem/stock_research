import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from backend.db.connection import async_session_maker


async def main() -> None:
    query = text(
        """
        SELECT enl.news_id,
               n.symbol,
               (n.embedding IS NOT NULL) AS has_embedding,
               n.embedding_model,
               enl.relevance_score,
               n.title
        FROM event_news_link enl
        JOIN news n ON n.id = enl.news_id
        WHERE enl.event_id = :eid
        ORDER BY enl.relevance_score DESC;
        """
    )

    async with async_session_maker() as session:
        rows = (await session.execute(query, {"eid": 1})).fetchall()

    print(f"event_id=1 links={len(rows)}")
    for r in rows:
        title = (r.title or "")
        print(
            f"news_id={r.news_id} sym={r.symbol} has_embedding={r.has_embedding} "
            f"model={r.embedding_model} score={r.relevance_score} title={title[:90]}"
        )


if __name__ == "__main__":
    asyncio.run(main())
