from sqlalchemy import create_engine
from sqlalchemy import ForeignKey, PrimaryKeyConstraint
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine("postgresql://postgres:a@localhost:5432/stocks")

Base = declarative_base()

def get_or_create(s, cls, **kwargs):
    ins = s.query(cls).filter_by(**kwargs).first()
    if not ins:
        ins = cls(**kwargs)
        s.add(ins)
        s.commit()
    return ins

class Stock(Base):
    __tablename__ = "stock"

    ticker = Column(String, index=True, primary_key=True)
    sector = Column(String)
    industry = Column(String)

    chart_data = relationship("ChartData")
    news = relationship("News")

    def __str__(self):
        return self.ticker

class ChartData(Base):
    __tablename__ = "chart_data"

    stock_ticker = Column(String, ForeignKey("stock.ticker"), index=True, primary_key=True)
    minute = Column(Integer, primary_key=True, index=True)

    # marketHigh
    high = Column(Float)

    # marketLow
    low = Column(Float)

    # marketAverage
    average = Column(Float)

    # marketVolume
    volume = Column(Float)

class News(Base):
    __tablename__ = "news"

    stock_ticker = Column(String, ForeignKey("stock.ticker"), index=True, primary_key=True)
    time = Column(DateTime, index=True, primary_key=True)

    headline = Column(String)
    summary = Column(String)
    related = Column(String)
