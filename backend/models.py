from sqlalchemy import Column, Integer, String, Float, DateTime
from database import Base
import datetime

class Backtest(Base):
    __tablename__ = "backtests" 
    id =Column(Integer,primary_key=True,index=True)
    symbol = Column(String, index=True)
    strategy = Column(String, default="SmaCross")
    starting_value = Column(Float)
    final_value = Column(Float)
    ran_at = Column(DateTime, default=datetime.datetime.utcnow)