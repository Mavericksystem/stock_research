from datetime import datetime
from sqlalchemy import (
    Column, String, Numeric, Date, DateTime, Boolean, ForeignKey, UniqueConstraint, Index, Integer, JSON
)
from sqlalchemy.orm import relationship
from backend.db.connection import Base
from sqlalchemy import Text
from pgvector.sqlalchemy import Vector

class Stock(Base):
    __tablename__ = 'stocks'

    symbol = Column(String, primary_key=True)
    name = Column(String(255))
    exchange = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    prices = relationship("Price", back_populates="stock", cascade="all, delete-orphan")
    indicators = relationship("TechnicalIndicator", back_populates="stock", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="stock", cascade="all, delete-orphan")

class Price(Base):
    __tablename__ = "prices"
    
    symbol = Column(String(20), ForeignKey("stocks.symbol"), primary_key=True)
    date = Column(Date, primary_key=True)

    open = Column(Numeric)
    high = Column(Numeric)
    low = Column(Numeric)
    close = Column(Numeric)
    volume = Column(Numeric)

    adj_open = Column(Numeric)
    adj_high = Column(Numeric)
    adj_low = Column(Numeric)
    adj_close = Column(Numeric)

    div_cash = Column(Numeric)
    split_factor = Column(Numeric)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    stock = relationship("Stock", back_populates="prices")

    __table_args__ = (
        UniqueConstraint("symbol", "date", name="uix_symbol_date"),
        Index("idx_symbol_date", "symbol", "date")
    )

class TechnicalIndicator(Base):
    __tablename__ = "technical_indicators"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), ForeignKey("stocks.symbol"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)

    daily_return = Column(Numeric(12, 6))
    return_7d = Column(Numeric(12, 6))
    sma_20 = Column(Numeric(12, 6))
    sma_50 = Column(Numeric(12, 6))
    rsi_14 = Column(Numeric(12, 6))
    volatility_20d = Column(Numeric(12, 6))
    
    price_vs_sma_20 = Column(Numeric(12, 6))
    price_vs_sma_50 = Column(Numeric(12, 6))

    created_at = Column(DateTime, default=datetime.utcnow)

    stock = relationship("Stock", back_populates="indicators")

    __table_args__ = (
        UniqueConstraint("symbol", "date", name="uix_symbol_date_indicator"),
        Index("idx_symbol_date_indicator", "symbol", "date")
    )

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), ForeignKey("stocks.symbol"), nullable=False, index=True)
    
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False, index=True)

    event_type = Column(String(50), nullable=False)
    source = Column(String(50), nullable=False, default="price") # price, news, volume
    
    magnitude = Column(Numeric(12, 6))
    normalized_score = Column(Numeric(12, 6), nullable=True) # z-score for ranking across stocks
    confidence = Column(Numeric(5, 4), nullable=True) # how sure are we this matters?
    
    context = Column(JSON, nullable=True) # {rsi: float, trend: str, price_vs_sma: float}

    resolved = Column(Boolean, default=False)
    explanation = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    stock = relationship("Stock", back_populates="events")

    __table_args__ = (
        Index("idx_symbol_date_event", "symbol", "start_date", "end_date"),
    )

class News(Base):
    __tablename__ = "news"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # v1: event-centeric assumption (one symbol per row). ok for phase 3
    symbol = Column(String(20), ForeignKey("stocks.symbol"), nullable=False, index=True)

    title = Column(String, nullable=True)
    content = Column(Text, nullable=True)

    source = Column(String(50), nullable=False)
    url = Column(String, nullable=False, unique=True)

    published_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    embedding = Column(Vector(384), nullable=True)
    embedding_model = Column(String, nullable=True)
    embedding_created_at = Column(DateTime(timezone=True), nullable=True)
    __table_args__ = (
        Index("idx_news_symbol_published_at", "symbol", "published_at"),
    )

class EventNewsLink(Base):
    __tablename__ = "event_news_link"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    news_id = Column(Integer, ForeignKey("news.id", ondelete="CASCADE"), nullable=False, index=True)

    relevance_score = Column(Numeric(12, 6), nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("event_id", "news_id", name="uix_event_news_link"),
        Index("idx_event_news_event_score", "event_id", "relevance_score"),
    )