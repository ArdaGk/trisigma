from src import Strategy
from src.toolkit import *
from functools import wraps
from time import time
from trisigma import time_utils
#Pending cancels!!!
#server time isn't tested
#Cancel response isn't added in broker
#Check if updates are actually working
#Format check at first
#Catch and report login error

class WebullAutoAlgo (Strategy):

    def start (self):
        self.latencies = {}
        self.clean_wallet()
        self.test_market_data()
        self.test_market_orders()
        self.test_limit_orders()

    def clean_wallet (self):
        self.broker.cancel_all()
        orders = self.broker.get_open_orders()
        pos = self.broker.get_position()
        a1 = _assert(list(pos.keys()) == ["full", "locked", "free"], false_msg="Broker.get_position keys are incorrect")
        count = len(orders['BUY']) + len(orders['SELL'])
        a2 = _assert(count == 0, false_msg="Limit orders cancelation failed")
        if pos > 0:
            self.broker.sell("MARKET", pos)
        elif pos < 0:
            self.broker.buy("MARKET", pos)
        self.broker()
        pos = self.broker.get_position()
        a3 = _assert(pos == 0, false_msg="Existing position could not be sold")
        return all([a1,a2,a3])

    def test_market_data(self):
        price = self.broker.get_price()
        _assert(isinstance(price, float) and price > 0, true_msg="Price data is accessible", false_msg="Price data is not accessible")
        assertions = []
        for interval, lookback in self.config_data["ohlc_size"]:
            df = self.broker.get_ohlc(interval, lookback)
            #secs is set to the amount of seconds in the interval
            secs = time_utils.to_timestamp(interval)
            #Calculate "time" difference between each row
            df["diff"] = df["time"].diff()
            #Delete every row where diff is greater than 16 hours
            new_df = df[df["diff"] < 16*60*60]
            #assert that every diff is equal to interval
            a1 = _assert((new_df["diff"] == secs).all(), false_msg="OHLC interval is not correct")
            #assert that the length of df is equal to lookback
            a2 = _assert(len(df) == lookback, false_msg="OHLC lookback is not correct")
            #append a1 and a2 into assertions
            assertions.append(a1)
            assertions.append(a2)
        return all(assertions)

    def test_market_orders(self):
        #Testing market buy
        bal1 = self.broker.get_balance()['full']
        resp = self.broker.buy("MARKET", 1)
        self.broker()
        bal2 = self.broker.get_balance()['full']

        a1 = _assert("orderId" in resp.keys(), false_msg="Unknown response for market buy")
        pos = self.broker.get_position()['full']
        a2 = _assert(pos == 1, false_msg="Market buy is not detected in Broker.get_position")
        a3 = _assert(bal2 < bal1, false_msg="Market buy is not detected in Broker.get_balance")
        orderId = self.broker.get_trades()[-1]["orderId"] if a1 else -1
        a4 = _assert(orderId == resp["orderId"], "Market buy is not detected in Broker.get_trades")

        #Testing market sell
        resp = self.broker.buy("MARKET", 1)
        self.broker()
        bal3 = self.broker.get_balance()['full']

        a5 = _assert("orderId" in resp.keys(), false_msg="Unknown response for market sell")
        pos = self.broker.get_position()['full']
        a6 = _assert(pos == 0, false_msg="Market sell is not detected in Broker.get_position")
        a7 = _assert(bal2 < bal3, false_msg="Market sell is not detected in Broker.get_balance")
        orderId = self.broker.get_trades()[-1]["orderId"] if a1 else -1
        a8 = _assert(orderId == resp["orderId"], "Market sell is not detected in Broker.get_trades")
        return all([a1,a2,a3,a4,a5,a6,a7,a8])

    def test_limit_orders(self):
        pass

def _assert (assertion, true_msg=None, false_msg=None):
    #if true print in green if false print in red
    if assertion:
        print(f"\033[92m{true_msg}\033[0m")
        return True
    else:
        print(f"\033[91m{false_msg}\033[0m")
        return False

