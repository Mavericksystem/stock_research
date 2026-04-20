from datetime import datetime
from sqlalchemy import(
    Column, String, Numeric, Date, DateTime, Boolean, ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from backend.db.connection import Base

class Stock(Base):
    __tablename__ = 'stocks'

    symbol = Column(String, primary_key=True)
    name = Column(String(255))
    exchange = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    prices = relationship("Price", back_populates="stock")

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