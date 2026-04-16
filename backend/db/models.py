from sqlalchemy import Column, Integer, String, Date, Numeric, BigInteger, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .connection import Base

class Stock(Base):
    __tablename__ = 'stocks'

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, index=True, nullable=False)
    name = Column(String)
    sector = Column(String)

    prices = relationship("Price", back_populates="stock")
    indicators = relationship("Indicator", back_populates="stock")
    news = relationship("News", back_populates="stock")

class Price(Base):
    __tablename__ = "prices"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    open = Column(Numeric)
    high = Column(Numeric)
    low = Column(Numeric)
    close = Column(Numeric)
    volume = Column(BigInteger)

    stock = relationship("stock", back_populates="indicators")

class News(Base):
    __tablename__ = "news"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False, index=True)
    title = Column(String)
    content = Column(String)
    source = Column(String)
    publishes_at = Column(DateTime)
    
    stock = relationship("stock", back_populates="news")