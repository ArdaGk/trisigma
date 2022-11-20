=========
Deployment
=========

Simply import the algo into main.py. Parameters of the live test are passed as a "CONF" dictionary

Sample
-----
.. highlight:: python
main.py
::
    from firstalgo import FirstAlgo
    from trisigma.livetest import LiveTest

    CONF = {'strategy':FirstAlgo,
            'load': {'15m': 96*2, '1w': 5},
            'freq': '5s',
            'platform': 'binance',
            'symbols': [{"symbol": "LINKSDT"}, {"symbol": "ETHUSDT"}],
            'api_key': "<api_key>",
            'secret_key': "<secret_key>",
            'label':"some_label",
            'fm': "./botdata/"}

    live = LiveTest(CONF)
    live.connect()

Main Parameters
--------------
* **strategy**: the algo as a class.
* **load**: The range of the historic data that will be needed. The data within this range will be cached for quicker access.
* **freq**: At what interval should the algo be called? Units: (s)econd, (m)inute, (h)our, (d)ay
* **platform**: The trading platform. (binance/ibkr)
* **fm**: The path where the data should be stored.
* **label**: A name for the bot. Data will be stored under this name, and it will be needed for data recovery.
* **symbols**: This is for the symbols that will be traded. Format: [{"symbol": <symbol>},]. This is also where symbol-specific parameters can be declared; Any additional key  passed can be accessed within the algo via self.config_data['<param_name>']
|
Platform-specific Parameters:
----------------------------
Binance:
=======
* **api_key**: this can be generated from binance.com
* **secret_key**: this can be generated from binance.com

IBKR:
====
* **mode**: Options: "ibg-real", "ibg-paper", "tws-real", "tws-paper".
* **addr**: the IP address of the client. Put "127.0.0.1" if client is in the same machine.
