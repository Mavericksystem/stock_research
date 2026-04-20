from datetime import datetime
from sqlalchemy import(
    Column, String, Numeric, Date, DateTime, Boolean, ForeignKey, UniqueConstraint, Index

)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Stock(Base):
    __tablename__ = 'stocks'

    symbol = Column(String, primary_key=True)
    name = Column(String((255)))
    exchange = Column(String((50)))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    prices = relationship("StockPrice", back_populates="stock")

class StockPrice(Base):
    __tablename__ = "prices"
    
    symbol = Column(string(20), Foreignkey("stocks.symbol"), primary_key=True)
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