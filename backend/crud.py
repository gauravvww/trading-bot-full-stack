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
