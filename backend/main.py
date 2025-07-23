import os
from dotenv import load_dotenv
import alpaca_trade_api as tradeapi #tradeapi is alias
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


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