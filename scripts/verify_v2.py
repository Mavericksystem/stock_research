import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from backend.db.connection import async_session_maker
from backend.ingestion.news_scraper import run_context_for_symbol

async def verify_and_inspect():
    print("1. Deleting old noisy links...")
    async with async_session_maker() as session:
        await session.execute(text("DELETE FROM event_news_link;"))
        await session.commit()

    print("2. Re-running news scraper with strict V2 model...")
    for sym in ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "JPM", "V", "WMT"]:
        await run_context_for_symbol(sym, days_back=10)

    print("3. Inspecting NEW filtered Top-K output...\n")
    query = """
    SELECT 
        e.symbol, 
        e.start_date, 
        e.event_type, 
        n.title, 
        enl.relevance_score
    FROM event_news_link enl
    JOIN events e ON enl.event_id = e.id
    JOIN news n ON enl.news_id = n.id
    ORDER BY e.symbol, e.start_date DESC, enl.relevance_score DESC;
    """
    async with async_session_maker() as session:
        res = await session.execute(text(query))
        rows = res.fetchall()
        
        print(f"--- TOTAL LINKS SURVIVED THE V2 FILTER: {len(rows)} ---\n")
        current_event = None
        for row in rows:
            symbol, date, event_type, title, score = row
            event_str = f"[{symbol}] {event_type} on {date}"
            if event_str != current_event:
                print(f"\nEVENT: {event_str}")
                current_event = event_str
            
            print(f"  -> (v2 Score: {score:.2f}) {title[:100]}...")

if __name__ == "__main__":
    asyncio.run(verify_and_inspect())