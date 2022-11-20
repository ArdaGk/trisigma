Trisigma
===========

.. toctree::
    :maxdepth: 2
    :caption: Contents:

    components
    backtesting
    deploy
    tuning
 
Main Features
~~~~~~~~~~~~
- Binance.com, Binance.us and Interactive Brokers integration
- Webull, Yahoo Finance and Binance historic data scraper.
- Backtesting and Strategy Optimizer.
- Google Sheets and Google Cloud Storage integration.
- Slack Channel Integration.
 
Platforms
~~~~~~~~
- Binance.com
- Binance.us
- Interactive Brokers (paper and live trade)

Quickstart
---------
``pip install trisigma``

Usage
-----
.. highlight:: python
Template for Binance live testing:
::
    from trisigma import Strategy
    from trisigma.livetest import LiveTest

    class FirstAlgo (Strategy):
        def setup (self): #This method will be called once the bot is launched.
            pass
        def update (self): #This method will be called at every interval.
            pass

    CONF = {'strategy':FirstAlgo,
            'load': {'15m': 96*2, '1w': 5},
            'freq': '5s',
            'platform': 'binance',
            'symbols': [{"symbol": "LINKSDT"}, {"symbol": "ETHUSDT"}],
            'api_key': "<api_key>",
            'secret_key': "<secret_key>",
            'label':"some_label",
            'fm': "./botdata/"}

Template is made up of two parts:
    1. **Strategy**: This is where the strategy details are specified. ``trisigma.Strategy``` class contains the necessary methods to access market data or send signals.
    2. **Configuration** This is where the testing details are specified. Some of these details include the brokerage (IBKR or Binance), tickers, credentials and path to save the data.
