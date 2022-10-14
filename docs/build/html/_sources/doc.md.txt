# trisigma Scripting API

## Contents
1. Base Class
2. Components
3. Built-in methods
4. Backtesting
5. Go Live
6. Strategy Optimizer


# Base Class
## class ```trisigma.Algorithm```
Base class for every algorithm. Includes the necessary built-in functions.
### class ```trisigma.Algorithm.broker```
Includes functions for, market data, account data, and actions (buy/sell)
### string ```trisigma.Algorithm.alg_stat```
Returns the state: 'init' for initialized, and "running" if running.
### string ```trisigma.Algorithm.config_data```
Includes instrument-specific parameters that are passed in the conf file
###  ```trisigma.Algorithm.register(func, trigger, args=[])```
Used to make certain functions triggered when a condition returns True.
##### Example 1
```python
self.register(self.sell_loss, self.trail.on_hit) 
#Call the custom method 'self.sell_loss' whenever self.trail.on_hit returns True. 
#(self.trail.on_hit is a method from Trailling_Loss that returns True whenever price is below the trail)
```
##### Example 2
```python
self.register(self.new_traces, Alarm(self.broker, '1w'))
#Call the custom method 'self.new_traces' Alarm(self.broker, '1w')() returns True.
#In this case "Alarm()" is a callable object that returns True on every new interval.
```
###  ```trisigma.Algorithm.bind(alg)``` --> trisigma.Algorithm
Creates a child algo that can be accessed within the current algo
##### Example 2
```python
self.child_algo = self.bind(ChildAlgo)
self.child_algo()
#Each Algorithym is a callable object. Calling it will trigger its "update" function
```

# Built-in Methods
These methods will be called by the base class only if they exist in the code.

### ```start ()```
Triggered for only once when the bot has started. This is where new methods should be added to the ```self.event_handler```

### ```update ()```
Triggered whenever the price changes

### ```late_update ()```
The very last method that will be called whenever the price changes. Can be used to execute the signals that were retuned during the ```update()```.

### ```end ()```
Will be triggered whenever the bot has been interrupted or shut down.

# Components
## *class* ```Broker```
Includes functions for, market data, account data, and actions (buy/sell). It is the only component that is built-in in the base class (self.broker), so no need to recreate. 

### Variables
Variables below are 'GET' only. They are auutomatically set and updated by the engine while the algorithm is running.
### *string* ```Broker.symbol```
Returns the instrument of the strategy. This is set automatically by the engine when the algorithm is running.
### *string* ```Broker.quote_asset```
Returns the quote asset (default: USD)
### *bool* ```Broker.buy_filled```
True, if an asset sold in that very current frame.
### *bool* ```Broker.sell_filled```
True, if an asset sold in that very current frame.

### Signals
### ```Broker.buy (_type, qty, limit_price = None)```
### ```Broker.quote_buy (_type, qty, quote_price, limit_price = None)```
Buy by USD instead of quantity
### ```Broker.sell (_type, qty, limit_price = None)```
### ```Broker.quote_sell (_type, qty, quote_price, limit_price = None)```
Sell by USD instead of quantity
### ```Broker.cancel (side, index)```
Cancels a particular open order by its index
### ```Broker.cancel_all (side)```
Cancels every (BUY or SELL) order
### Account Data
### ```Broker.get_open_orders ()``` --> dict
Returns a dict with two keys: BUY and SELL. each containing a list of orders
### ```Broker.get_position ()``` --> dict
Returns a dict with three keys: "FREE": spendable assets, "LOCKED": assets that are waiting to be limit sold, "FULL": FREE + LOCKED
### ```Broker.get_balance ()``` --> dict
Returns a dict with three keys: "FREE": spendable quote asset, "LOCKED": quote asset locked for limit buy, "FULL": FREE + LOCKED
### Market Data
### ```Broker.get_ohlc (interval, lookback = 1)``` --> dict
Get the candlestick of the 'interval'. Includes open/high/sell/low
### ```Broker.get_price (lookback = 1)``` --> float
### ```Broker.get_time ()``` --> datetime
### ```Broker.get_timestamp () ``` --> float
### ```Broker.get_bids ()``` --> list
### ```Broker.get_asks ()``` --> list
### ```Broker.get_buy_price ()``` --> float
Returns the price we would pay if we were to do Market Buy
### ```Broker.get_sell_price ()``` --> float
Returns the price we would get if we were to do Market Sell

## *class* Alarm
A component that can be used to trigger in the beginning of a certain interval
### Intervals
* 1w
* 1d
* 1h
* 30m
* 15m
* 1m
* 1s

Coefficients can be anything. (Ex: 43m would work just fine)

### ```Alarm.__init__ (broker, interval, delta=None)```
- *Broker* broker: needs ```self.broker``` in order to access the current time
- *string* interval: one of those intervals. (Case sensitive)
- *timedelta* delta: offset for the certain unit. Ex/ (self.broker, '1w', delta=timedelta(days=6)) indicates every week's Sunday (not Monday)

### ```Alarm.__call__ () --> bool```
The ```Alarm```, as an object, must be called in every frame so it can process the current ```self.broker.get_time()``` and return True/False. There is no need to do this manually. Adding the object into base class' event handler (```self.event_handler.add```) will make the base class automatically call this object in every iteration.

## *class* Trailling_Loss
A certain percentage below the current price can be easily tracked via this class.

### ```Trailling_Loss.__init__ (broker, perc)```
- *Broker* broker: It also needs ```self.broker``` in order to access the current price
- *float* perc: How much below? Ex/ 0.975, for %2.5

### ```Trailling_Loss.__call__ () --> bool```
Just like ```Alarm```, the class, as an object, must be called in every iteration so it can update the trail. Except this time the Base class won't be able to do it manually (yet). Syntax for calling.
### ```Trailling_Loss.on_hit ()``` --> *bool*
Returns true if the price went below the trail.

### Sample Usage
```python
class Alg_v1 (Algorithm):
  def start (self):
    self.trail = Trailling_Loss(self.broker, 0.975)
    self.event_handler.add(self.sell_all, self.trail.on_hit) # Call sell_all whenever price is below the trail.

  def update (self):
    self.trail() #Must be called in every iteration, so it can update the trail based on new price.  

  def sell_all (self):
    #Sell all
```

## *class* Traces
### ```Traces.__init__ (broker)```
- *Broker* broker: again, needs self.broker in order to access certain market datas
### ```Traces.__call__ (broker)```
Must also be called manually in every iteration so that it can update its variables.
### ```Traces.set_traces (new_traces)```
Updates the traces with the given
### ```Traces.get_traces ()``` --> *dict*
Returns the traces
### ```Traces.get_region ()``` --> *int*
Returns the region. format: [..., -2, -1, 0, 1, 2, ...] where 0 is the white region, positives top, negatives below.
### ```Traces.is_inside (region, ohlc)``` --> *bool*
Returns true if the all of the given candles ("ohlc") are  inside the "region"
### ```Traces.on_change ()``` --> *bool*
Returns true whenever the current price crosses a trace. Passing this to the event handler will automatically trigger the desired function when a trace is crossed.
### Sample Usage
```python
class Alg_v1 (Algorithm):
  def start(self):
      self.traces = Traces(self.broker)
      self.traces.set_traces(get_new_traces()) 
      self.event_handler.add(self.sell_profit, self.traces.on_change) # Call sell_profit whenever self.traces.on_change returns True

  def update(self):
      self.traces() #Again must be called every iterations

  def sell_profit (self):
      if self.traces.region == 1:
        #Sell the positions
    
```
## Other useful modules/classes

### *class* trisigma.Sock
A socket-based event handler. Triggers given function whenever desired message is sent from another socker host.

### *class* trisigma.Slack
Slack channel integration

### *module* trisigma.sheets
Google sheets integration

### *module* trisigma.cloud_storage
Google Cloud Storage integration

### *module* trisigma.yahoo
Yahoo finance integration

### *module* trisigma.filemanager
Provides a platform-independent and easier way to interact with the disk.

### *module* trisigma.pots
Includes different ways of handling the capital.

### *module* trisigma.evaluation_utils
Library to calculate different metrics like return and sharp ratio

# Backtesting
## Syntax
```python
from trisigma.backtesting import Backtesting
from my_alg import Alg

conf = {'alg': Alg,
		'intervals': ['5m', '1w', '15m', '1h'],
		'freq': '5m',
		'balance': 500,
		'lookback': 365,
		'delta': timedelta(days=7),
		'name': "link1y",
		'symbols': [{'symbol': 'LINKUSDT'}, {'symbol': 'ETHUSDT'}],
		'source': 'binance'
		'fm': "/home/arda/alg_data/"}
		
test = Backtesting(conf)
test.run(steps=3)
```

### *class* Backtesting
### ```__init__ (conf, **kwargs)```
##### Configuration parameters:
* "alg": The algorithm as a ***class***. Initialization will be done by the "Backtesting" class without any arguments.
* "symbols": Symbols (Instruments) that should be tested. Any additional keys inside these dictionaries will be accessible within the class via ```self.config_data```. Therefore, instrument-specific parameters should be included in here.
* "intervals": Candlestick intervals that will be needed for the strategy. These intervals will be automatically cached by the engine for quicker access.
* "freq": Main interval of backtest.
* "lookback": How much past should the backtest go
* "delta": Skips the given amount of time before starting the test. It is useful when we need access to past candlesticks that normally won't be recorded within the test.
*  "balance": Grand balance
*  "source": market data source. "binance" for crypto, "webull" for securities
* "name" (optional). Market data that is pulled will be saved in the disk with the given name.
* "fm": Path for the data to be saved.

### ```run(steps=1)```
Starts the backtest.
* steps: how many interval to jump over in each iteration. This comes handy when we need to speed up the test.

***Note:*** steps=3 for the main interval: '5m' doesn't always mean "every 15 minutes". This is because tradeless time frames are automatically ignored.

# Go Live
## Syntax
```python
import stream
from my_alg import Alg

conf = {
'alg': Alg,
'freq': '5m',
'balance': 5000,
'load': {'15m': 10, '1w': 2},
'platform': "ibkr-paper",
'symbols': [{'symbol': "AAPL"},
			{'symbol': "NFLX"},
			{'symbol'} "META"}],
'fm': "/home/arda/alg_data"]
stream = Stream(conf)
stream.connect(ip="127.0.0.1")
```

### *class* trisigma.stream.Stream
### ```__init__ (conf, **kwargs)```
##### Configuration parameters:
* "alg": The algorithm as a ***class***. Initialization will be done by the "Backtesting" class without any arguments.
* "symbols": Symbols (Instruments) that will be traded. Any additional keys inside these dictionaries will be accessible within the class via ```self.config_data```. Therefore, instrument-specific parameters should be included in here.
* "intervals": Candlestick intervals that will be needed for the strategy. These intervals will be automatically cached by the engine for quicker access. Unlike the ```Backtesting``` conf, intervels here are in the form of dictionaries. Each value represents how much candles to go back.
* "freq": Main interval of stream.
*  "balance": Grand balance
*  "platform": Brokerage platform. options: "binance", "ibkr-paper", "ibkr-real"
* "fm": Path for the data to be saved.

(Any of these keys can also be passed through **kwargs)

### ```connect (ip=None)```
Starts the stream.
 * ip: client server address for "ibkr-paper" or "ibkr-real". No need for "binance"

# Strategy Optizer
## Syntax
```python
from trisigma import *
from trisigma.tuner import Tuner
import os
import time

conf = {
    "label": "talg_gen1",
    "alg": "talg_gen1.py",
    "parameters":
    {
        "__data__": [["linktune3y", ["LINKUSDT"]]],
        "stop_loss": [2.5, 3, 4]
        "close": [true, false],
        "wait15": [true, false],
        "candles": [4, 6, 8, 10, 12, 14, 16],
    },
}

tuner = Tuner(conf, max_child=CHILD, offset=OFFSET, fm='/home/arda/alg_data')
tuner.launch()
```

### *class* trisigma.tuner.Tuner
### ```__init__ (conf, **kwargs)```
##### Configuration parameters:
* "alg": The algorithm as a ***module***. this module will be run by the ***Tuner***'s subprocessor with an additional argument: parameters.
* "label": Name given to the tuning process.
* "parameters": Inside, there should be the parameters to be optimized. Each value has to be a list containing the possible parameters. "_ _ data _ _" is a mandatory special parameter that indicates the desired market. This is the same label that is saved through ***Backtesting***'s "name" key.

### ```launch ()```
Starts the tuner.

***Note***: the ***Tuner*** does not expect or save any output. Saving must be handled within the algo.
