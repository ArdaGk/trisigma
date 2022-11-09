from binance.spot import Spot
from datetime import datetime, timedelta
import math
import copy


class Broker:

    def __init__(self, symbol, balance, client, label=None):
        pass
    def __call__(self):
        """Updates broker attributes (price, position, balance, time)"""
        pass 
    def buy(self, _type, qty, limit_price=None):
        """Buy a certain quantity from an asset.
        :param _type: "LIMIT" or "MARKET"
        :param qty: quantity
        :param limit_price: Limit price for _type="LIMIT"
        """
        pass
    def quote_buy(self, _type, quote_price, limit_price=None):
        """Buy an asset with a quote price.
        :param _type: "LIMIT" or "MARKET"
        :param quote_price: amount of asset to purchase with the quote price.
        :param limit_price" limit price for _type="LIMIT"
        """
        pass
    def sell(self, _type, qty, limit_price=None):
        """Sell a certain quantity from an asset.
        :param _type: "LIMIT" or "MARKET"
        :param qty: quantity
        :param limit_price: Limit price for _type="LIMIT"
        """
        pass
    def quote_sell(self, _type, quote_price, limit_price=None):
        """Sell an asset with a quote price.
        :param _type: "LIMIT" or "MARKET"
        :param quote_price: amount of asset to sell with the quote price.
        :param limit_price" limit price for _type="LIMIT"
        """
        pass
    def cancel(self, orderId):
       """Cancel an existing open order
       :param orderId: the order id which to cancel.
       """
       pass 
    def cancel_all(self):
      """Cancel every open order"""
        pass
    def get_open_orders(self):
        """Returns a list of open orders"""
        pass

    def get_trades(self):
        """Returns previous trades"""
         pass

    def get_position(self):
        """Returns the position including those that are locked"""
        pass

    def get_balance(self, reserved=True):
        if reserved:
            return self.balance
        else:
            return -1

    def get_ohlc(self, interval, lookback=1):
        return self.client.klines[self.symbol][interval][:lookback]

    def get_price(self, lookback=1):
        return self.client.quotes[self.symbol]['price']

    def get_time(self, of_trade=False):
        return datetime.now()

    def get_timestamp(self, of_trade=False):
        time = datetime.now().timestamp()
        return time

    def get_bids(self):
        return self.client.quotes[self.symbol]['bidPrice']

    def get_asks(self):
        return self.client.quotes[self.symbol]['askPrice']

    def get_sell_price(self):
        return self.get_bids()

    def get_buy_price(self):
        return self.get_asks()

    def on_trade(self, side='all', _type='all'):
        output = {}
        last_buy = max(
            [trd['time'] for trd in self.client.trades[self.symbol] if trd['isBuyer']] + [-1])
        last_sell = max(
            [trd['time'] for trd in self.client.trades[self.symbol] if not trd['isBuyer']] + [-1])

        output['BUY'] = last_buy not in [self.__trade_buffer['BUY'], -1]
        output['SELL'] = last_sell not in [self.__trade_buffer['SELL'], -1]
        output['all'] = output['BUY'] or output['SELL']

        self.__trade_buffer['BUY'] = last_buy
        self.__trade_buffer['SELL'] = last_sell

        return output[side]

    def __save(self, order):
        typ = order['type']
        ts = order['time']
        stats = fm.load(f"{self.label}_stats")
        stats['open_orders'].append(ts)
        times = [ord['time'] for ord in self.client.orders[self.broker.symbol]]
        new_orders = [t for t in stats['orders'] if t in times]
        stats['open_orders'] = new_orders
        self.fm.save(stats, f"{self.label}_stats")
