import os
from dotenv import load_dotenv
import alpaca_trade_api as tradeapi #tradeapi is alias
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import backtrader as bt
from datetime import datetime
from strategies.SmaCross import SmaCross
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import crud, models
from database import SessionLocal, engine

# This line creates the "backtests" table in the PostegreSQL database I have connected/installed, if it doesn't exist
models.Base.metadata.create_all(bind=engine)


os.environ['MPLBACKEND'] = 'Agg'
load_dotenv()
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
    "http://localhost",
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

@app.get("/api/backtest/{symbol}")
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
            