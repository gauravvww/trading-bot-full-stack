from sqlalchemy.orm import Session
import models

def create_backtest_result(db: Session, symbol_passed:str,  starting_value_passed: float, final_value_passed: float):
    db_backtest = models.Backtest(
        symbol = symbol_passed,
        starting_value = starting_value_passed,
        final_value = final_value_passed
    )

    db.add(db_backtest)
    db.commit()
    db.refresh(db_backtest)
    return db_backtest
def create_live_trade(db: Session, symbol_passed: str, side_passed: str, quantity_passed: float, price_passed: float):
    db_trade = models.LiveTrade(
        symbol=symbol_passed,
        side=side_passed,
        quantity=quantity_passed,
        filled_avg_price=price_passed
    )
    db.add(db_trade)
    db.commit()
    return db_trade
