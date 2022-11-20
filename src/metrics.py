from datetime import datetime, timedelta
import numpy as np
from . import Globals

class Metrics:
    def __init__ (self, broker, _id = "default"):
        self.broker = broker
        self.balance = broker.get_balance()['full']

        self.alloc_hist = []
        self._id = _id
        if _id not in Globals.variables.keys():
            Globals.variables[_id]={''}

    def get_return (self, trades, rng:timedelta = None):
        trades = self.broker.trades
        if rng != None:
            trades = list(filter(lambda trd: trd['time'] > (datetime.now() - rng).timestamp(), trades))
        
        holding = self.broker.get_position()['full'] * self.broker.get_price()
        return holding + sum([float(trd['price']) * float(trd['qty']) if trd['side'] == 'SELL' else float(-trd['price']) * float(trd['qty']) for trd in trades])

    def get_sharp_ratio(self, returns, risk_free_rate=0.0298):
        return (sum(returns) - risk_free_rate) / np.std(returns)



