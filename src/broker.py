class Broker:

    def __call__(self):
        """Updates broker attributes (price, position, balance, time)"""
        return
    def buy(self, typ, qty, limit_price=None):
        """Buy a certain quantity from an asset.

        :param typ: "LIMIT" or "MARKET"
        :type typ: string
        :param qty: quantity
        :type qty: float
        :param limit_price: Limit price if typ="LIMIT"
        :type limit_price: float
        """
        return
    def quote_buy(self, typ, quote_price, limit_price=None):
        """Buy an asset with a quote price.

        :param typ: "LIMIT" or "MARKET"
        :type typ: string
        :param quote_price: amount of asset to purchase with the quote price.
        :type quote_price: float
        :param limit_price" limit price if typ="LIMIT"
        """
        return
    def sell(self, typ, qty, limit_price=None):
        """Sell a certain quantity from an asset.

        :param typ: "LIMIT" or "MARKET"
        :type typ: string
        :param qty: quantity
        :type qty: float
        :param limit_price: Limit price if typ="LIMIT"
        """
        return
    def quote_sell(self, typ, quote_price, limit_price=None):
        """Sell an asset with a quote price.

        :param typ: "LIMIT" or "MARKET"
        :type typ: string
        :param quote_price: amount of asset to purchase with the quote price.
        :type quote_price: float
        :param limit_price" limit price if typ="LIMIT"
        """
        return
    def cancel(self, orderId):
        """Cancel an existing open order

        :param orderId: the order id which to cancel.
        """
        return
    def cancel_all(self):
        """Cancel every open order"""
        return
    def get_open_orders(self):
        """Returns a list of open orders"""
        return

    def get_trades(self):
        """Returns the trade history"""
        return

    def get_position(self):
        """Returns the position including those that are locked"""
        return

    def get_balance(self, reserved=True):
        """Returns the balance (quote asset) of the account"""
        return

    def get_ohlc(self, interval, lookback=1):
        """Returns previous candles

        :param interval: candle interval eg. "1h"
        :type interval: string
        :param lookback: how many candles to return
        :type lookback: int
        """
        return

    def get_price(self):
        """Returns the price of the symbol"""
        return

    def get_time(self):
        """Returns the time as <datetime>"""
        return

    def get_timestamp(self):
        """Returns the timestamp as an <int>"""
        return

    def get_bids(self):
        """Returns the best bid"""
        return

    def get_asks(self):
        """Returns the best ask"""
        return

    def get_sell_price(self):
        """Returns the sell price based on the best bid"""
        return

    def get_buy_price(self):
        """Returns the buy price based on the best ask"""
        return

    def on_trade(self, side='all', _type='all'):
        """Returns True if there was a trade since the last time this function is called, (this is NOT a pure function, if it returns True, the new trade will be stored)

        :param side: Checks a specific side:  'BUY', 'SELL', 'all' (default).
        :param side: string
        :param typ: Checks a specific order type: 'MARKET', 'LIMIT', 'all' (default).
        :param typ: string
        """
        return
