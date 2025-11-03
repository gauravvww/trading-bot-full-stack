"""SQLAlchemy ORM models for persisting backtests and live trades."""

from sqlalchemy import Column, DateTime, Float, Integer, String, func

from database import Base


class Backtest(Base):
    __tablename__ = "backtests"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    strategy = Column(String, default="SmaCross")
    starting_value = Column(Float)
    final_value = Column(Float)
    ran_at = Column(DateTime(timezone=True), server_default=func.now())


class LiveTrade(Base):
    __tablename__ = "live_trades"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    side = Column(String)
    quantity = Column(Float)
    filled_avg_price = Column(Float)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
