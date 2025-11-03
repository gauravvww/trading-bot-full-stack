"""FastAPI application wiring Alpaca, Backtrader, and the database."""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Dict

import alpaca_trade_api as tradeapi
import backtrader as bt
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

import crud
import models
from database import SessionLocal, get_db, init_db

sys.path.append("..")
from strategies.SmaCross import SmaCross


logger = logging.getLogger(__name__)


def _build_alpaca_client() -> tradeapi.REST:
    """Initialise the Alpaca REST client, raising a clear error if keys are missing."""

    key_id = os.getenv("APCA_API_KEY_ID")
    secret_key = os.getenv("APCA_API_SECRET_KEY")
    if not key_id or not secret_key:
        raise RuntimeError(
            "Set APCA_API_KEY_ID and APCA_API_SECRET_KEY environment variables before starting the API."
        )

    return tradeapi.REST(
        key_id,
        secret_key,
        "https://paper-api.alpaca.markets",
        api_version="v2",
    )


app = FastAPI()
api = None


@app.on_event("startup")
def on_startup() -> None:
    """Ensure database tables exist and initialise external clients."""

    global api  # noqa: WPS420 - mutated during startup only

    init_db()
    api = _build_alpaca_client()
    logger.info("Application startup complete")


origins = [
    "http://localhost:3000",
    "https://trading-bot-full-stack.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/status")
def get_status() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/api/account")
def get_account_info() -> Dict[str, str]:
    if api is None:  # pragma: no cover - startup guard
        raise HTTPException(status_code=503, detail="Alpaca client not initialised yet")

    try:
        account = api.get_account()
        return {
            "account_number": account.account_number,
            "cash": account.cash,
            "portfolio_value": account.portfolio_value,
            "buying_power": account.buying_power,
            "status": account.status,
        }
    except Exception as exc:  # pragma: no cover - proxy error to client
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/api/backtest/{symbol}")
def run_backtest(symbol: str, db: Session = Depends(get_db)) -> Dict[str, object]:
    if api is None:  # pragma: no cover - startup guard
        raise HTTPException(status_code=503, detail="Alpaca client not initialised yet")

    try:
        cerebro = bt.Cerebro()
        cerebro.broker.setcash(100000)

        data_df = api.get_bars(
            symbol,
            "1Day",
            start="2022-01-01",
            end=datetime.now().strftime("%Y-%m-%d"),
            feed="iex",
        ).df
        if data_df.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for symbol {symbol}",
            )

        data_df["openinterest"] = 0
        cerebro.adddata(bt.feeds.PandasData(dataname=data_df))
        cerebro.addstrategy(SmaCross)
        cerebro.run()

        start_val = 100000.0
        end_val = round(cerebro.broker.getvalue(), 2)
        crud.create_backtest_result(
            db=db,
            symbol_passed=symbol,
            starting_value_passed=start_val,
            final_value_passed=end_val,
        )

        data_df["timestamp"] = data_df.index.strftime("%Y-%m-%d")

        return {
            "symbol": symbol,
            "starting_value": start_val,
            "final_value": end_val,
            "chart_data": data_df.to_dict(orient="records"),
        }
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - bubble unexpected errors to client
        raise HTTPException(status_code=500, detail=str(exc)) from exc


live_tasks: Dict[str, bool] = {}


async def run_live_trade(symbol: str) -> None:
    if api is None:  # pragma: no cover - startup guard
        logger.error("Live trading requested before Alpaca client initialised")
        return

    db = SessionLocal()
    logger.info("Starting live trade task for %s", symbol)
    try:
        while live_tasks.get(symbol):
            try:
                latest_bars = api.get_bars(symbol, "1Day", limit=50, feed="iex").df
                if latest_bars.empty:
                    await asyncio.sleep(60)
                    continue

                latest_bars["openinterest"] = 0
                cerebro = bt.Cerebro()
                cerebro.adddata(bt.feeds.PandasData(dataname=latest_bars))
                cerebro.addstrategy(SmaCross)

                results = cerebro.run()
                latest_signal = results[0].crossover[0]

                positions = {position.symbol: position for position in api.list_positions()}

                if symbol not in positions and latest_signal > 0:
                    order = api.submit_order(
                        symbol=symbol,
                        qty=1,
                        side="buy",
                        type="market",
                        time_in_force="day",
                    )
                    crud.create_live_trade(
                        db=db,
                        symbol_passed=symbol,
                        side_passed="buy",
                        quantity_passed=1,
                        price_passed=float(order.filled_avg_price or 0),
                    )
                elif symbol in positions and latest_signal < 0:
                    order = api.submit_order(
                        symbol=symbol,
                        qty=positions[symbol].qty,
                        side="sell",
                        type="market",
                        time_in_force="day",
                    )
                    crud.create_live_trade(
                        db=db,
                        symbol_passed=symbol,
                        side_passed="sell",
                        quantity_passed=float(positions[symbol].qty),
                        price_passed=float(order.filled_avg_price or 0),
                    )

                await asyncio.sleep(60)
            except Exception as exc:  # pragma: no cover - keep loop alive
                logger.exception("Error in live trading loop for %s: %s", symbol, exc)
                await asyncio.sleep(60)
    finally:
        db.close()
        live_tasks.pop(symbol, None)
        logger.info("Live trade task for %s has stopped", symbol)


@app.post("/api/livetrade/start/{symbol}")
def start_live_trade(symbol: str, background_tasks: BackgroundTasks) -> Dict[str, str]:
    if api is None:  # pragma: no cover - startup guard
        raise HTTPException(status_code=503, detail="Alpaca client not initialised yet")

    if symbol in live_tasks:
        raise HTTPException(
            status_code=400,
            detail="Live trading for this symbol is already running.",
        )

    live_tasks[symbol] = True
    background_tasks.add_task(run_live_trade, symbol)
    return {"message": f"Live trading started for {symbol}."}


@app.post("/api/livetrade/stop/{symbol}")
def stop_live_trade(symbol: str) -> Dict[str, str]:
    if symbol not in live_tasks:
        raise HTTPException(
            status_code=404,
            detail="Live trading for this symbol is not running.",
        )

    live_tasks.pop(symbol, None)
    return {"message": f"Live trading stopped for {symbol}."}
