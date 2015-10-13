from __future__ import print_function

try:
    import Queue as queue
except ImportError:
    import queue   # This is what Queue is called in Python 3.x
import time
import pprint
import os
import pandas as pd

from qsforex import settings


class MultiBacktest(object):
    """
    Enscapsulates the settings and components for carrying out
    an event-driven backtest on the foreign exchange markets.
    
    Essentially the same as the code in backtest.py, but this allows for 
    multiple strategy hyperparameters to be tested in one code run.
    """
    def __init__(
        self, pairs, data_handler, strategy, 
        strat_params_list, portfolio, execution, 
        equity=100000.0, heartbeat=0.0, 
        max_iters=10000000000):
        """
        Initialises the backtest.
        """
        self.pairs = pairs
        self.events = queue.Queue()
        self.csv_dir = settings.CSV_DATA_DIR
        self.strat_params_list = strat_params_list
        self.equity = equity
        self.heartbeat = heartbeat
        self.max_iters = max_iters

        self.data_handler_cls = data_handler
        self.strategy_cls = strategy
        self.portfolio_cls = portfolio
        self.execution_cls = execution


    def _generate_trading_instances(self, strategy_params_dict):
        """
        Generates the trading instance objects from their class types.
        """
        print("Creating DataHandler, Strategy, Portfolio, and ExecutionHandler for")
        print("stragegy parameter list: %s..." % strategy_params_dict)
        self.ticker = self.data_handler_cls(self.pairs, self.events, self.csv_dir)
        self.strategy = self.strategy_cls(
            self.pairs, self.events, **strategy_params_dict
        )
        self.portfolio = self.portfolio_cls(
            self.ticker, self.events, equity=self.equity, backtest=True
        )
        self.execution = self.execution_cls()


    def _run_backtest(self):
        """
        Carries out an infinite while loop that polls the 
        events queue and directs each event to either the
        strategy component of the execution handler. The
        loop will then pause for "heartbeat" seconds and
        continue unti the maximum number of iterations is
        exceeded.
        """
        print("Running Backtest...")
        iters = 0
        while iters < self.max_iters and self.ticker.continue_backtest:
            try:
                event = self.events.get(False)
            except queue.Empty:
                self.ticker.stream_next_tick()
            else:
                if event is not None:
                    if event.type == 'TICK':
                        self.strategy.calculate_signals(event)
                        self.portfolio.update_portfolio(event)
                    elif event.type == 'SIGNAL':
                        self.portfolio.execute_signal(event)
                    elif event.type == 'ORDER':
                        self.execution.execute_order(event)
            time.sleep(self.heartbeat)
            iters += 1

    def _output_performance(self):
        """
        Outputs the strategy performance from the backtest.
        """
        print("Calculating Performance Metrics...")
        return self.portfolio.output_results()
        # Lots missing here.  See p. 152.
    
    def simulate_trading(self):
        """
        Simulates the backtest and outputs portfolio performance for each set
        of strategy parameters passed.
        """
        out_filename = "multiBacktestResults.csv"
        resultsDir = settings.OUTPUT_RESULTS_DIR
        out_file = os.path.join(resultsDir, out_filename)
        out = open(out_file, "w")
        
        spl = len(self.strat_params_list)
        for i, sp in enumerate(self.strat_params_list):
            print("Strategy %s out of %s..." % (i+1, spl))
            self._generate_trading_instances(sp)
            self._run_backtest()
            stats = self._output_performance()
            pprint.pprint(stats)
            
            tot_ret = float(stats[0][1].replace("%",""))
            cagr = float(stats[1][1].replace("%",""))
            sharpe = float(stats[2][1])
            max_dd = float(stats[3][1].replace("%",""))
            dd_dur = int(stats[4][1])
            
            out.write(
                "%s,%s,%s,%s,%s,%s,%s\n" % (
                sp["short_window"], sp["long_window"],
                tot_ret, cagr, sharpe, max_dd, dd_dur))
                
        out.close()
            
        
        self._run_backtest()
        self._output_performance()
        print("Backtest complete.")
