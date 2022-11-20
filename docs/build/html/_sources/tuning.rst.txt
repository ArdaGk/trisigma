============================
Hyper Parameter Optimization
============================

.. autoclass:: src.tuner.Tuner
   :members: launch
   :special-members: __init__



Sample
-----
.. highlight:: JSON
config.json
::
    {
        "parameters":
        {
            "trailling_stop_loss_perc":[0.99, 0.985,0.98, 0.975],
            "capital_dist": [[0.99, 0], [0.75, 0.24], [0.50, 49]],
            "profit_perc": [0.02, 0.03, 0.04],
        },
        "market":
        {
            "symbols": ["LINKUSDT"],
            "length": 365,
            "freq": "5m"
        }
    }

|
.. highlight:: python
main.py
::
    from firstalgo import FirstAlgo
    from trisigma.tuning import Tuner

    FM = "./data/"
    CONF_FILE = "config.json"

    with open(CONF_FILE, 'r') as file:
        conf = json.load(file)

    tuner = Tuner(FM, conf, FirstAlgo, label="firstTuning", max_child=4)
    tuner.launch()


* "parameters" key is where the hyper parameters should be stored. These will be accessible inside the Strategy object via ``self.config_data["param_name"]``
* "market" keys determine the backtest market data.
