import sys
import os 
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import select, and_, not_, exists
from sqlalchemy.ext.asyncio import async_sessionmaker

from backend.db.models import TecnicalIndicator, Event
from backend.db.connection import engine

sessionLocal = async_sessionmaker(engine, expire_on_commit=False)

