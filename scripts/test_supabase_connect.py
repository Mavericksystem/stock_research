import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DATABASE_URL = "postgresql+asyncpg://postgres:Vector297343108@db.nnuqcazhwsprmksqieoi.supabase.co:5432/postgres"

engine = create_async_engine(DATABASE_URL)

async def test():
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            print('OK:', result.scalar())
    except Exception as e:
        import traceback, sys
        traceback.print_exc()
        print('ERROR:', str(e), file=sys.stderr)

if __name__ == '__main__':
    asyncio.run(test())
