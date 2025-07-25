import os

import alpaca_trade_api as tradeapi #tradeapi is alias
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import backtrader as bt
from datetime import datetime

from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import crud, models
from database import SessionLocal, engine
import asyncio
import sys
sys.path.append('..')
from strategies.SmaCross import SmaCross


# This line creates the "backtests" table in the PostegreSQL database I have connected/installed, if it doesn't exist
models.Base.metadata.create_all(bind=engine)



api = tradeapi.REST(
    os.getenv('APCA_API_KEY_ID'),
    os.getenv('APCA_API_SECRET_KEY'),
    'https://paper-api.alpaca.markets',
     api_version='v2'

    #created an object of REST class from alpaca_trade_api as tradeapi
)

app = FastAPI()



origins = [
    "http://localhost:3000",
    "https://trading-bot-full-stack.vercel.app" 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True, #useful for login which i am not going to implement as of now, but sort of boilerplate config, causes no harm
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/status")
def get_status():
 return {"status": "ok"} #FastAPI converts this toJSON

@app.get("/api/account")
def get_account_info():
    try:
     account = api.get_account()
     return{
       "account_number": account.account_number,
       "cash": account.cash,
       "portfolio_value": account.portfolio_value,
       "buying_power": account.buying_power, #alpaca has 2:1 leverage for intraday
       "status": account.status,
     }
    except Exception as e:
        return {"error": str(e)} 
    #if there is an error, return the error message as a string
    #str is necessary because the Exception e is an object, not a string so FastAPI will not be able to convert it to JSON

@app.post("/api/backtest/{symbol}")
def run_backtest(symbol, db: Session = Depends(get_db)):
       
        try:
            cerebro = bt.Cerebro()
            cerebro.broker.setcash(100000)

            data_df = api.get_bars(
                        symbol,
                        '1Day',
                        start = '2022-01-01',
                        end = datetime.now().strftime('%Y-%m-%d'),
                        feed = 'iex' #i want free data, premium data source sip is not available free in alpaca
                        ).df
            if data_df.empty:
                raise HTTPException(status_code=404, detail=f"No data found for symbol {symbol}")
            print(data_df.head())
            data_df['openinterest'] = 0 # Backtrader requires this column, even if it's not used, check safari bookmark
            feed = bt.feeds.PandasData(dataname = data_df)
            cerebro.adddata(feed)
            cerebro.addstrategy(SmaCross)
            print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
            cerebro.run()
            print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
            start_val = 100000.0
            end_val = round(cerebro.broker.getvalue(), 2)
            crud.create_backtest_result(db=db, symbol_passed=symbol, starting_value_passed=start_val, final_value_passed=end_val)
            data_df['timestamp'] = data_df.index.strftime('%Y-%m-%d')  #index renamed as timestamp is in string format for plotting
            chart_data_list = data_df.to_dict(orient='records')
           

                # chart_data_list = [
                #   {'timestamp': '2025-07-20', 'open': 100, 'close': 110},
                #   {'timestamp': '2025-07-21', 'open': 110, 'close': 108}
                #  ]

            return {
                "symbol" : symbol,
                "starting_value": 100000,
                "final_value": round(cerebro.broker.getvalue(),2),
                "chart_data": chart_data_list,
            }
        except Exception as e:
           raise HTTPException(status_code=500,detail=str(e))
            
live_tasks = {}

async def run_live_trade(symbol:str):
    db = SessionLocal()
    print(f"Satrting live trade task for {symbol} ")
    try:
        while symbol in live_tasks:
            try:
                print(f"Checking for signals for {symbol}...")
                latest_bars = api.get_bars(symbol, '1Day', limit=50, feed='iex').df
                if latest_bars.empty:
                    await asyncio.sleep(60)  # Wait for 1 minute before retrying
                    continue
                latest_bars['openinterest'] = 0
                data_feed = bt.feeds.PandasData(dataname=latest_bars)

                cerebro = bt.Cerebro()
                cerebro.adddata(data_feed)
                cerebro.addstrategy(SmaCross)
                
                results = cerebro.run()
                latest_signal = results[0].crossover[0]

                print(f"Latest signal for {symbol}: Crossover={latest_signal}")

                positions = {p.symbol: p for p in api.list_positions()}
                # api.list_positions() → [
                #     Position(symbol='AAPL', qty=1),
                #      Position(symbol='TSLA', qty=1)
                # ]
                # positions = {
                #     'AAPL': Position(symbol='AAPL', qty=1),
                #     'TSLA': Position(symbol='TSLA', qty=1)
                # }


                if symbol not in positions and latest_signal > 0:
                    print(f"BUY SIGNAL for {symbol}. Submitting market order.")
                    order = api.submit_order(symbol=symbol, qty=1, side='buy', type='market', time_in_force='day')
                    crud.create_live_trade(db=db, symbol_passed=symbol, side_passed='buy', quantity_passed=1, price_passed=float(order.filled_avg_price))
        
                elif symbol in positions and latest_signal < 0:
                    print(f"SELL SIGNAL for {symbol}. Submitting market order to close position.")
                    order = api.submit_order(symbol=symbol, qty=positions[symbol].qty, side='sell', type='market', time_in_force='day')
                    crud.create_live_trade(db=db, symbol_passed=symbol, side_passed='sell', quantity_passed=1, price_passed=float(order.filled_avg_price))
                else:
                    print(f"No signal for {symbol}. Holding position.")

            except Exception as e:
                print(f"Error in live trade task for {symbol}: {e}")
            await asyncio.sleep(60)
    finally:
        db.close()
        print(f"Live trade task for {symbol} has been stopped.")            

@app.post("/api/livetrade/start/{symbol}")
def start_live_trade(symbol: str, background_tasks: BackgroundTasks):
    if symbol in live_tasks:
        raise HTTPException(status_code=400, detail="Live trading for this symbol is already running.")
    
    live_tasks[symbol] = True
    background_tasks.add_task(run_live_trade, symbol)
    return {"message": f"Live trading started for {symbol}."}

@app.post("/api/livetrade/stop/{symbol}")
def stop_live_trade(symbol: str):
    if symbol not in live_tasks:
        raise HTTPException(status_code=404, detail="Live trading for this symbol is not running.")
    
    
    del live_tasks[symbol]
    return {"message": f"Live trading stopped for {symbol}."}