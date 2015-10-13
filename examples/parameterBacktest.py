from __future__ import print_function

from qsforex.backtest.backtest_multiParam import MultiBacktest
from qsforex.execution.execution import SimulatedExecution
from qsforex.portfolio.portfolio import Portfolio
from qsforex import settings
from qsforex.strategy.strategy import MovingAverageCrossStrategy
from qsforex.data.price import HistoricCSVPriceHandler
from itertools import product

if __name__ == "__main__":
    # Define what instruments to trade.
    # Trade on GBP/USD and EUR/USD
    #pairs = ["GBPUSD", "EURUSD"]  # For FX trading.
    pairs = ["GBPUSD"]  # For FX trading.
    #symbol_list = ['ARES', 'WLL']  # For pairs trading.
    
    # Create the strategy parameter grid.
    # Parameters for MovingAverageCrossStrategy
    strat_shortWindow = [100, 300, 900]
    strat_longWindow = [1000, 2000, 3000]
    # Use the cartesian product generator to get a list of
    # all parameter combinations.
    strat_params_list = list(product(
        strat_shortWindow, strat_longWindow
    ))
    # Convert this to a list of dicts.
    strat_params_dict_list = [
        dict(short_window = sp[0], long_window = sp[1])
        for sp in strat_params_list
    ]

    # Create and execute the backtest
    multiBacktest = MultiBacktest(
        pairs, HistoricCSVPriceHandler, 
        MovingAverageCrossStrategy, strat_params_dict_list, 
        Portfolio, SimulatedExecution, 
        equity=settings.EQUITY
    )
    multiBacktest.simulate_trading()