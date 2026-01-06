from sqlalchemy import Column, Integer, String, Float, DateTime, func
from database import Base
import datetime

class Backtest(Base):
    __tablename__ = "backtests" 
    id =Column(Integer,primary_key=True,index=True)
    symbol = Column(String, index=True)
    strategy = Column(String, default="SmaCross")
    starting_value = Column(Float)
    final_value = Column(Float)
    ran_at = Column(DateTime(timezone=True), server_default=func.now()) #check safari bookmark
class LiveTrade(Base):
    __tablename__ = "live_trades"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    side = Column(String) # 'buy' or 'sell'
    quantity = Column(Float)
    filled_avg_price = Column(Float) # Average price at which the order was filled, even though I am just taking one qty of one stock, this is good for scaling
    timestamp = Column(DateTime(timezone=True), server_default=func.now())