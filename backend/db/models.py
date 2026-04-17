from sqlalchemy import Column, Integer, String, Date, Numeric, BigInteger, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .connection import Base


class Stock(Base):
    __tablename__ = 'stocks'

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, index=True, nullable=False)
    name = Column(String)
    sector = Column(String)

    prices = relationship("Price", back_populates="stock", cascade="all, delete-orphan")
    indicators = relationship("Indicator", back_populates="stock", cascade="all, delete-orphan")
    news = relationship("News", back_populates="stock", cascade="all, delete-orphan")


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

    stock = relationship("Stock", back_populates="prices")


class Indicator(Base):
    __tablename__ = "indicators"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    rsi = Column(Numeric)
    sma_20 = Column(Numeric)
    sma_50 = Column(Numeric)
    volatility = Column(Numeric)

    stock = relationship("Stock", back_populates="indicators")


class News(Base):
    __tablename__ = "news"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False, index=True)
    title = Column(String)
    content = Column(String)
    source = Column(String)
    published_at = Column(DateTime)
    
    stock = relationship("Stock", back_populates="news")