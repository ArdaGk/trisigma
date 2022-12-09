class Broker:

    def __call__(self):
        """Updates broker attributes (price, position, balance, time). This magic method will be called automatically by the base class before each check, therefore there is no need to call it within the strategy."""
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
        """Buy an asset with a quote price (e.g. buy $100 worth of LINK instead of 18 LINK)

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
        """Sell an asset with a quote price. (e.g. sell $100 worth of LINK instead of 18 LINK)

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
    def cancel_all(self, side='all'):
        """Cancel every open order

        :param side: This can be used to cancel only a specific side ("BUY" or "SELL", default: "all")
        :type side: string
        """
        return
    def get_open_orders(self):
        """
        :return: A list of open orders
        :rtype: list
        
        .. highlight:: python
        .. code-block:: python

            # Format of open order dictionary:
            {
                "orderId": <int>,
                "time": <int>, #timestamp
                "symbol": <str>,
                "side" : <str>,
                "price": <float>,
                "origQty": <float>,
                "filledQty": <float>,
                "status": <str>, # "NEW", "PARTIALLY_FILLED", "REJECTED", "EXPIRED", "PENDING_CANCEL"
                "timeInForce": <str> # Only "GTC" for now.
                "type": <str>, # Only "LIMIT" for now.
            }
        """
        return

    def get_trades(self):
        """
        :return: A list of trades made by this account.
        :rtype: list
        
        .. highlight:: python
        .. code-block:: python

            # Format of trade dictionary:
            {
                "orderId": <int>,
                "time": <int>, #timestamp
                "symbol": <str>,
                "side" : <str>,
                "price": <float>,
                "qty": <float>,
                "quoteQty": <float>,
                "type": <str>, # "LIMIT", "MARKET"
                "commission": <float>,
                "commissionAsset": <float>
            }
        """
        return

    def get_position(self):
        """
        :return: The position including those that are locked.

        .. highlight:: python
        .. code-block:: python

            # Format of ticker position:
            {"full": <float>, "free": <float>, "locked": <float>}

            # full: total ammount of asset owned.
            # free: amount of asset that can be traded.
            # locked: amount of asset that is already in a open order.
        """
        return

    def get_balance(self, reserved=True):
        """
        :return: The overall balance (quote asset) of the account. This output represents the capital. ("USD", "USDT", "EUR" etc.)

        .. highlight:: python
        .. code-block:: python

            # Format of account balance:
            {"full": <float>, "free": <float>, "locked": <float>}

            # full: total ammount of capital
            # free: amount of asset capital that can be used to buy an asset.
            # locked: amount of capital that is locked due to a open order (limit buy).
        """

        return

    def get_ohlc(self, interval, lookback=1):
        """
        :param interval: candle interval eg. "1h"
        :type interval: string
        :param lookback: how many candles to return
        :type lookback: int

        :return: Previous candles.
        :rtype: pandas.DataFrame
        """
        return

    def get_price(self):
        """
        :return: The price of the symbol.
        """
        return

    def get_time(self):
        """
        The output is not equal to datetime.now(), the time returned is the one given by the target brokerage firm.

        :return: The time of the target server.
        :rtype: datetime.datetime
        """
        return
    def get_timestamp(self):
        """
        | The output is same as get_time().timestamp()
        | The output is not equal to datetime.now().timestamp(), the time returned is the one given by the target brokerage firm.

        :return: The timestamp of the target server.
        :rtype: int
        """
        return

    def get_bid(self):
        """
        :return: The best bid in the order book.
        :rtype: float
        """
        return

    def get_ask(self):
        """
        :return: The best ask in the order book.
        :rtype: float
        """
        return

    
    def on_trade(self, side='all', typ='all'):
        """Returns True if there was a trade since the last time this function is called, (this is NOT a pure function, if it returns True, the new trade will be stored)

        :param side: Checks a specific side:  'BUY', 'SELL', 'all' (default).
        :type side: string
        :param typ: Checks a specific order type: 'MARKET', 'LIMIT', 'all' (default).
        :type typ: string
        """
        return
