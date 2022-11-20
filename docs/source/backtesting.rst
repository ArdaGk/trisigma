===========
Backtesting
===========

Simply import the algo into main.py. Parameters of the backtest are passed as a "CONF" dictionary

Sample
-----
.. highlight:: python
main.py
::
    from firstalgo import FirstAlgo
    from trisigma.backtesting import Backtesting
    from datetime import timedelta

    CONF = {'strategy':FirstAlgo,
            'intervals': ['5m', '1w', '15m', '1h'],
            'freq': '5s',
            'lookback': 365,
            'delta': timedelta(days=7),
            'balance': 10000,
            'symbols': [{"symbol": "LINKSDT"}, {"symbol": "ETHUSDT"}],
            'name': "1y_data",
            'source': "binance",
            'fm': "./data/"}

    test = Backtesting(CONF)
    test.run()

Parameters
--------------
* **strategy**: the algo as a class.
* **intervals**: The candlestick intervals that will be needed. Unlike livetest, backtesting doesn't require range for candles, this is all the candles from past will be cached.
* **freq**: At what interval should the algo be called? This value has to be the smallest among those in the 'intervals'.  Units: (s)econd, (m)inute, (h)our, (d)ay
* **lookback**: How past should the backtest extend (in days)
* **delta**: This is basically an offset for the backtest's start time. For example, if the algo needs 2 weeks of past data in order to calculate SMA, then delta should be set totimedelta(days=14) in order to prevent IndexError.
* **symbols**: This is for the symbols that will be traded. Format: [{"symbol": <symbol>},]. This is also where symbol-specific parameters can be declared; Any additional key  passed can be accessed within the algo via self.config_data['<param_name>']
* **name**: (Optional), giving a name will automatically store the scraped market data in the disk. Next time the algo is backtested with the same name, market data in the disk will be used instead.
* **source**: Source of market data. (binance/webull)
* **fm**: The path where the data should be stored.

