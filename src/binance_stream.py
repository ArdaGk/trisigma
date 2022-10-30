from binance.spot import Spot
from datetime import datetime, timedelta
from .reserved_binance import ReservedSpot
import math
import copy
VERSION = "v1.0.4"
print(f"binance_stream running {VERSION}")

class Client:
  def __init__ (self, api, secret, symbols, fm):
    self.spot = Spot(api, secret, show_limit_usage=True)
    self.spot = ReservedSpot(api, secret, show_limit_usage=True, label="test", fm=fm)
    self.quotes = {}
    self.klines = {}
    self.positions = {}
    self.orders = {}
    self.trades = {}

    self.fuel = 0
    self.weight = 0
    self.weight_hist = [-1]
    self.limit = 0
    self.order_count = 0
    self.delta = 0
    self.latency = 0
    self.server_time = 0
    self.ex_info = {}
    self.acc_info = {}
    self.symbols = symbols
    self.setup()
    self.positions_buffer = {}
    self.updatables = copy.deepcopy(symbols)
    self.block = False
    self.quote_asset = 'USDT'

    self.fm = fm

  def setup (self):
    self.update_exchange()
    self.ping()
    for sym in self.symbols:
      self.quotes[sym] = {'price': 0, 'bidPrice': 0, 'bidQty': 0, 'askPrice': 0, 'askQty': 0}
      self.klines[sym] = {}
      self.orders[sym] = {}
      self.trades[sym] = {}

  def cancel (self, symbol, orderId):
    self.spot.cancel_order(symbol, orderId=orderId)

  def cancel_all (self, symbol):
    self.spot.cancel_open_orders(symbol)

  def trade(self, *argv, **kwargs):
    try:
      self.block = False
      rules = list(filter(lambda x: x['symbol'] == argv[0], self.ex_info['symbols']))[0]
      price_filter = list(filter(lambda x: x['filterType'] == 'PRICE_FILTER', rules['filters']))[0]
      lot_size = list(filter(lambda x: x['filterType'] == 'LOT_SIZE', rules['filters']))[0]
      if 'quantity' in kwargs.keys():
        size = 1 / float(lot_size['stepSize'])
        kwargs['quantity'] = round(math.floor(kwargs['quantity'] * size) / size,9)
      if 'price' in kwargs.keys():
        size = 1 / float(price_filter['tickSize'])
        kwargs['price'] = round(math.floor(kwargs['price'] * size) / size,9)

      if argv[0] not in self.updatables:
        self.updatables.append(argv[0])

      resp = self.spot.new_order(*argv, **kwargs)
      return resp
    except Exception as e:
      self.fm.log('binance_logs', str(e))
      self.fm.log('binance_logs_extra', str(argv))
      self.fm.log('binance_logs_extra', str(kwargs))

  def generic_update(self):
    self.update_quote() #2
    self.update_balances() #10


  def symbol_update(self, symbol=None):
    try:
      if not self.block:
        self.generic_update()
        self.ping() #1
        self.block=True
      if symbol in self.updatables:
        self.update_orders(symbol) #5
        self.update_trades(symbol) #10
        self.updatables.remove(symbol)
    except Exception as e:
      self.fm.log('binance_logs_update', str(e))

  def ping(self):
    ts1 = datetime.now().timestamp() * 1000
    st = self.spot.time()
    self.update_weight(st)
    ts2 = datetime.now().timestamp() * 1000
    self.latency = ts2 - ts1
    self.delta = (ts1 + int(self.latency/2)) - st['data']['serverTime']
    self.server_time = st['data']['serverTime']

  def update_klines(self, symbol, interval, limit):
    klines = self.spot.klines(symbol, interval, limit=limit)
    self.update_weight(klines)
    output = []
    for r in reversed(klines['data']):
      entry = {'time': float(r[0]), 'open': float(r[1]), 'high': float(r[2]), 'low': float(r[3]), 'close': float(r[4]),  'volume': float(r[5])}
      output.append(entry)
    self.klines[symbol][interval] = output

  def update_exchange(self):
    ex_info = self.spot.exchange_info()
    self.update_weight(ex_info)

    self.ex_info = ex_info['data']
    m_limit = list(filter(lambda x: x['interval'] == 'MINUTE', ex_info['data']['rateLimits']))[0]['limit']
    self.limit = m_limit

  def update_orders(self, symbol):
    orders = self.spot.get_open_orders(symbol)
    self.update_weight(orders)

    self.orders[symbol] = orders['data']

  def update_trades(self, symbol):
    trades = self.spot.my_trades(symbol)
    self.update_weight(trades)

    self.trades[symbol] = trades['data']

  def update_quote(self):
    depths = self.spot.book_ticker(symbols=self.symbols)
    prices = self.spot.ticker_price(symbols=self.symbols)
    for v in depths['data']:
      entry = {'price': float(self.quotes[v['symbol']]['price']), 
               'bidPrice': float(v['bidPrice']), 
               'bidQty': float(v['bidQty']), 
               'askPrice': float(v['askPrice']), 
               'askQty': float(v['askQty'])}
               
      self.quotes[v['symbol']] = entry
    for v in prices['data']:
      self.quotes[v['symbol']]['price'] = float(v['price'])

    self.update_weight(depths)

  def update_balances(self):
    acc_info = self.spot.account()
    self.update_weight(acc_info)
    self.acc_info = acc_info

    for bal in acc_info['data']['balances']:
      free = self.round_qty(float(bal['free']), bal['asset'] + self.quote_asset, key='symbol', notional=True)
      locked = self.round_qty(float(bal['locked']), bal['asset'] + self.quote_asset, key='symbol')
      full = free + locked
      self.positions[bal['asset']] = {'full': full, 'free': free, 'locked': locked}
  
    self.changed_assets()

  def round_qty(self, num, symbol, key='baseAsset', notional=False):
    try:
      rules = list(filter(lambda x: x[key] == symbol, self.ex_info['symbols']))[0]

      lot_size = list(filter(lambda x: x['filterType'] == 'LOT_SIZE', rules['filters']))[0]
      min_notional = list(filter(lambda x: x['filterType'] == 'MIN_NOTIONAL', rules['filters']))[0]['minNotional']

      elligible = symbol in self.quotes.keys() and notional
      if elligible and float(min_notional) >= self.quotes[symbol]['price'] * num:
        return 0

      size = 1 / float(lot_size['stepSize'])
      output = round(math.floor(num * size) / size,9)

      return output
    except IndexError as a:
      return 0

  def changed_assets(self):
    if self.positions_buffer == {}:
      self.positions_buffer = copy.deepcopy(self.positions)

    elif self.positions_buffer != self.positions:
      for asset in self.positions.keys():
        if asset in self.positions_buffer.keys() and self.positions[asset] != self.positions_buffer[asset] and asset != self.quote_asset:
          symbol = asset + self.quote_asset
          if symbol not in self.updatables:
            self.updatables.append(asset + self.quote_asset)

      self.positions_buffer = copy.deepcopy(self.positions)
    else:
      pass
      #print('No change')

  def update_weight(self, data):
    if type(data) == dict and 'limit_usage' in data.keys():
      if type(data['limit_usage']) == dict:
        if 'x-mbx-used-weight-1m' in data['limit_usage'].keys():
          new_weight = float(data['limit_usage']['x-mbx-used-weight-1m'])
          if new_weight <= self.weight:
            self.weight_hist.append(self.weight)
          else:
            self.weight_hist[-1] = new_weight
          self.weight = new_weight
        else:
          print('Limit response Error')
          values = [float(value) for value in data['limit_usage'].values()]
          self.weight = max(values)

  def reset_weights(self):
    self.weight_hist = [-1]

class Broker:

    def __init__(self, symbol, balance, client, label=None):
        self.client = client
        self.symbol = symbol
        self.quote_asset = 'USDT'
        self.start_balance = balance
        self.balance = balance
        self.position = 0
        self.open_orders = {'BUY': [], 'SELL': []}
        self.trades = {}
        self.__init_time = self.client.server_time - 86400
        self.__trade_buffer = {'BUY': -1, 'SELL': -1}
        self.label = label

    def __call__(self):

        self.client.symbol_update(self.symbol)
        trades = self.client.trades[self.symbol]
        for trd in trades:
          trd['side'] = 'BUY' if trd['isBuyer'] else 'SELL'
          trd['price'] = float(trd['price'])
          trd['qty'] = float(trd['qty'])
          trd['quoteQty'] = float(trd['quoteQty'])
          trd['commission'] = float(trd['commission'])
        self.trades = trades
        for freq in self.client.klines[self.symbol].keys():
          limit = len(self.client.klines[self.symbol][freq])
          self.client.update_klines(self.symbol, freq, limit)

        #Orders update
        self.open_orders['BUY'] = list(
            filter(lambda x: x['side'] == 'BUY', self.client.orders[self.symbol]))
        self.open_orders['SELL'] = list(
            filter(lambda x: x['side'] == 'SELL', self.client.orders[self.symbol]))

        #Balance update
        buys = list(filter(lambda x: x['isBuyer'], self.client.trades[self.symbol]))
        spent = sum([float(buy['quoteQty']) for buy in buys])
        sells = list(filter(lambda x: not x['isBuyer'], self.client.trades[self.symbol]))
        earned = sum([float(sell['quoteQty']) for sell in sells])

        full = earned - spent + self.start_balance
        locked = sum([float(ord['price']) * float(ord['origQty'])
                     for ord in self.open_orders['BUY']])
        free = full - locked
        self.balance = {'full': full, 'free': free, 'locked': locked}

        #New full balance update
        self.balance = self.client.positions[self.quote_asset]

        #Position Update
        asset = self.symbol[:-len(self.quote_asset)]
        self.position = self.client.positions[asset]


    def buy(self, _type, qty, limit_price=None):
      if _type == 'MARKET':
        return self.client.trade(self.symbol, 'BUY', _type, quantity=qty)
      elif _type == 'LIMIT':
        return self.client.trade(self.symbol, 'BUY', _type, quantity=qty, price=limit_price, timeInForce='GTC')

    def quote_buy(self, _type, quote_price, limit_price=None):
        if _type == 'MARKET':
            qty = quote_price / self.get_price()
            return self.buy('MARKET', qty)
        if _type == 'LIMIT':
            qty = quote_price / limit_price
            return self.buy('LIMIT', qty, limit_price)

    def sell(self, _type, qty, limit_price=None):
      if _type == 'MARKET':
        return self.client.trade(self.symbol, 'SELL', _type, quantity=qty)
      elif _type == 'LIMIT':
        return self.client.trade(self.symbol, 'SELL', _type, quantity=qty, price=limit_price, timeInForce='GTC')

    def quote_sell(self, _type, quote_price, limit_price=None):
        if _type == 'MARKET':
            qty = quote_price / self.get_price()
            return self.sell('MARKET', qty)
        if _type == 'LIMIT':
            qty = quote_price / limit_price
            return self.sell('LIMIT', qty, limit_price)

    def cancel(self, orderId):
        try:
          return self.client.cancel(self.symbol, orderId=orderId)
        except Exception as a:
          #print(a)
          return a

    def cancel_all(self):
        try:
          return self.client.cancel_all(self.symbol)
        except Exception as a:
          #print(a)
          return a

    def get_open_orders(self):
        return self.open_orders

    def get_trades(self):
        return self.trades

    def get_position(self):
        return self.position

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
