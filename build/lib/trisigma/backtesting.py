import pandas as pd
from datetime import datetime, timedelta
from trisigma.filemanager import FileManager
from .alg_exceptions import err
from .time_utils import ceil, to_timestamp_split
from copy import deepcopy
import trisigma.scraper as scraper

class Backtesting:
    def __init__(self, conf=None, fm=None, **kwargs):
        conf = conf | kwargs
        self.conf = conf
        self.alg = conf['alg']
        self.symbols = [sym['symbol'] for sym in conf['symbols']]
        self.intervals = conf['intervals']
        self.lookback = timedelta(days=conf['lookback'])
        self.source = conf['source']
        self.main = conf['freq']

        Broker.balance = conf['balance']
        self.name = None
        self.delta = timedelta(days=0)
        if 'delta' in conf.keys():
            self.delta = conf['delta']

        if 'name' in conf.keys():
            self.name = conf['name']
        if fm == None:
            if "fm" in conf.keys():
                fm = FileManager(conf['fm'])
            else:
                fm = FileManager()
        self.fm = fm
        self.setup()

    def setup(self):
        self.data = self.load_data()
        self.klines = {}
        self.algs = {}
        for symbol in self.conf['symbols']:
            sym = symbol['symbol']
            self.algs[sym] = self.alg()
            self.algs[sym].setup(Broker(self, sym), self.fm, config_data=symbol)
            self.klines[sym] = dict([(freq, [[
                {'time': 0, 'open': 0, 'high': 0, 'low': 0, 'close': 0}], 0]) for freq in self.intervals])

        #self.data.loc[self.data['symbol'] == 'UNIUSDT'].iloc[0]['time'] + self.delta
        self.start = {sym['symbol']: self.data.loc[self.data['symbol'] == sym['symbol']].iloc[0]['time'] + self.delta for sym in self.conf['symbols']}
    def run(self, step = 1):
        for row in self.data.iterrows():
            if row[0] % step == 0:
                if row[1]['time'].to_pydatetime() > self.start[row[1]['symbol']]:
                    self.set_klines(row[1])
                    resp = self.algs[row[1]['symbol']]()
                    if resp == 'disconnect':
                        return
                else:
                    self.set_klines(row[1])
        [alg.shutdown(force=False) for alg in self.algs.values()]

    def set_klines(self, new_row):

        sym = new_row['symbol']
        new_row['time'] = new_row['time'].timestamp()

        for k in self.klines[sym].keys():
            kline = deepcopy(self.klines[sym][k][0][-1])

            if k == self.main:
                self.klines[sym][k][0].append(new_row)

            else:
                if new_row['time'] >= self.klines[sym][k][1]:
                    self.klines[sym][k][1] = ceil(
                        new_row['time'], k).timestamp()
                    self.klines[sym][k][0].append(new_row)
                else:
                    kline['high'] = max(kline['high'], new_row['high'])
                    kline['low'] = min(kline['low'], new_row['low'])
                    kline['close'] = new_row['close']

                    self.klines[sym][k][0][-1] = kline

    def load_data(self):

        if self.source == 'binance':
            if self.name == None:
                data = scraper.binance(self.symbols, self.lookback, self.main)
            else:
                try:
                    data = pd.read_csv(self.fm.dir['data'] + f'markets/{self.name}_df.csv')
                except FileNotFoundError:   
                    data = scraper.binance(self.symbols, self.lookback, self.main)  
                    path = self.fm.dir['data'] + f'markets/{self.name}_df.csv'
                    data.to_csv(path)


        elif self.source == 'webull':
            m = to_timestamp_split(self.main)
            interval = m[0] * round(m[1] / 60)
            if self.name == None:
                data = scraper.webull(self.symbols, interval, self.lookback.days)
            else:
                try:
                    data = pd.read_csv(self.fm.dir['data'] + f'markets/{self.name}_df.csv')
                except FileNotFoundError:
                    data = scraper.webull(self.symbols, interval, self.lookback.days)
                    path = self.fm.dir['data'] + f'markets/{self.name}_df.csv'
                    data.to_csv(path)

        data["time"] = pd.to_datetime(data["time"], unit='ms')
        return data




    def __resample(self, tick, interval):
        interval = interval.replace('m','min')
        dt = tick.set_index('time')
        dt = dt['price'].resample(interval).ohlc().dropna().reset_index()
        return dt



class Broker:

    balance = 0
    __locked = {}
    def __init__(self, source, symbol):

        self.source = source
        self.open_orders = {'BUY': [], 'SELL': []}
        self.print_errors = True
        self.raise_errors = False
        self.commision_rate = 0.00075
        self.commision_cut = 0
        self.start_balance = Broker.balance
        self.__full_bal = self.start_balance
        self.__full_pos = 0
        self.position = self.get_position()
        self.balance = self.get_balance()
        self.__file_buffer = []
        self.symbol = symbol
        self.trades = []

    def __call__(self):
        self.__file_orders()
        Broker.__locked[self.symbol] = sum([ord['price'] * ord['qty'] for ord in self.get_open_orders()['BUY']])
        self.position = self.get_position()
        self.balance = self.get_balance()



    def buy(self, _type, qty, limit_price=None, forced_price=None):
        return self.__trade('BUY', _type, qty, limit_price, forced_price)

    def quote_buy(self, _type, quote_price, limit_price=None, forced_price=None):
        if limit_price == None:
            price = self.get_buy_price()
        else:
            price = limit_price
        qty = quote_price / price
        return self.__trade('BUY', _type, qty, price, forced_price)

    def sell(self, _type, qty, limit_price=None, forced_price=None):
        return self.__trade('SELL', _type, qty, limit_price, forced_price=forced_price)

    def quote_sell(self, _type, quote_price, limit_price=None, forced_price=None):
        if limit_price == None:
            price = self.get_sell_price()
        else:
            price = limit_price
        qty = quote_price / price
        return self.__trade('SELL', _type, qty, price, forced_price)

    def cancel(self, side, index):
        self.open_orders[side].remove(self.open_orders[side][index])

    def cancel_all(self, side):
        self.open_orders[side] = []

    def get_open_orders(self):
        return self.open_orders

    def get_position(self):
        locked = sum([ord['qty'] for ord in self.get_open_orders()['SELL']])
        free = self.__full_pos - locked
        return {'full': self.__full_pos, 'free': free, 'locked': locked}

    def get_balance(self):
        locked = sum(list(Broker.__locked.values()))
        full = Broker.balance
        free = full - locked
        return {'full': full, 'free': free, 'locked': locked}


    def get_ohlc(self, interval, lookback = 1):
        klines = list(
            reversed(self.source.klines[self.symbol][interval][0][1:][-lookback:]))
        klines = [dict(row) for row in klines]
        return klines

    def get_price(self, lookback = 1):
        return self.source.klines[self.symbol][self.source.main][0][-1]['close']

    def get_time(self):
        row = self.source.klines[self.symbol][self.source.main][0][-1]['time']
        return datetime.fromtimestamp(row) 

    def get_timestamp(self):
        return self.source.klines[self.symbol][self.source.main][0][-1]['time']


    def get_bids(self):
        pass

    def get_asks(self):
        pass

    def get_sell_price(self):
        ratio = 0.99999
        return self.get_price() * ratio

    def get_buy_price(self):
        ratio = 1.00001
        return self.get_price() * ratio

    def __is_fillable(self, side, qty, price):
        return (side == 'BUY' and price >= self.get_buy_price()) or (side == 'SELL' and price <= self.get_sell_price())

    def __file_orders(self):

        for ord in self.get_open_orders()['BUY']:
            if self.__is_fillable('BUY', ord['qty'], ord['price']):
                self.__file_buffer.append({'side': 'BUY', 'type':'LIMIT'})
                self.open_orders['BUY'].remove(ord)
                cost = ord['price'] * ord['qty']
                self.__full_pos += ord['qty']
                self.__full_bal -= cost
                self.commision_cut += cost * self.commision_rate
                entry = {'symbol': self.symbol, 'side': 'BUY', 'type': 'LIMIT', 'qty': ord['qty'], 'price': ord['price'], 'quoteQty': ord['qty'] * ord['price'], 'time': self.get_timestamp()}
                self.trades.append(entry)
                Broker.balance -= cost




        for ord in self.get_open_orders()['SELL']:
            if self.__is_fillable('SELL', ord['qty'], ord['price']):
                self.__file_buffer.append({'side': 'SELL', 'type': 'LIMIT'})
                self.open_orders['SELL'].remove(ord)
                cost = ord['price'] * ord['qty']
                self.__full_pos -= ord['qty']
                self.__full_bal += cost
                self.commision_cut += cost * self.commision_rate
                entry = {'symbol': self.symbol, 'side': 'SELL', 'type': 'LIMIT', 'qty': ord['qty'], 'price': ord['price'], 'quoteQty': ord['qty'] * ord['price'], 'time': self.get_timestamp()}
                self.trades.append(entry)
                Broker.balance += cost



    def on_trade(self, side='all', _type='all'):
        if len(self.__file_buffer) != 0:
            cond1 = self.__file_buffer[-1]['side'] == side or side == 'all'
            cond2 = self.__file_buffer[-1]['type'] == _type or _type == 'all'
            if cond1 and cond2:
                self.__file_buffer = []
                return True
        return False

    def __trade(self, side, _type, qty, limit_price=None, forced_price=None):
        if qty == 0:
            return

        if _type.upper() == 'LIMIT':

            if limit_price == None:
                return err('Limit price is empty', self.print_errors, self.raise_errors)

            if (side == 'BUY' and self.get_balance()['free'] < limit_price * qty) or (side == 'SELL' and self.get_position()['free'] < qty):
                return err('Insufficient balance.', self.print_errors, False)

            if not self.__is_fillable(side, qty, limit_price):
                entry = {'time': self.get_timestamp(), 'qty': qty, 'price': limit_price,  'quoteQty': qty * limit_price,}
                self.open_orders[side].append(entry)



            else:
                return self.__trade(side, 'MARKET', qty)

        else:
            if side == 'BUY':
                price = self.get_buy_price() if forced_price == None else forced_price
                cost = price * qty
                if cost <= self.get_balance()['free']:
                    self.__full_bal -= cost
                    self.__full_pos += qty
                    self.commision_cut += cost * self.commision_rate
                    entry = {'symbol': self.symbol, 'side': side, 'type': _type,
                             'qty': qty, 'price': price, 'quoteQty': qty * price, 'time': self.get_timestamp()}
                    self.trades.append(entry)
                    self.__file_buffer.append({'side': 'BUY', 'type': 'MARKET'})
                    Broker.balance -= cost


                else:
                    return err('Insufficient balance', self.print_errors, self.raise_errors)
            if side == 'SELL':
                price = self.get_sell_price() if forced_price == None else forced_price
                cost = price * qty
                if qty <= self.get_position()['free']:
                    self.__full_bal += cost
                    self.__full_pos -= qty
                    self.commision_cut += cost * self.commision_rate
                    entry = {'symbol': self.symbol, 'side': side, 'type': _type,
                             'qty': qty, 'price': price, 'quoteQty': qty * price, 'time': self.get_timestamp()}
                    self.trades.append(entry)
                    self.__file_buffer.append({'side': 'SELL', 'type': 'MARKET'})
                    Broker.balance += cost

                else:
                    return err('Insufficient balance', self.print_errors, self.raise_errors)


