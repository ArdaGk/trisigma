import json
import time
import socket
import threading
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta, tzinfo
from dateutil import tz
from .alg_exceptions import *
from .alg_events import *
import requests
import gspread
import numpy as np


class Algorithm:

    def __call__(self):
        try:
            if self.auto_broker:
                self.broker()

            if self.alg_stat == 'running':
                self.call_builtins('update')
                self.call_events()
                self.call_builtins('late_update')

            if self.alg_stat == 'init':
                self.call_builtins('start')
                self.alg_stat = 'running'

        except Disconnected as exc:
            return "disconnect"

    def setup(self, broker, fm, master=None, auto_broker = True, config_data = {}):
        self.alg_stat = 'init'
        self.stats = {}
        self.event_handler = BaseListener()
        self.broker = broker
        self.symbol = broker.symbol
        self.globals = {}
        self.fm = fm
        self.master = master
        self.auto_broker = auto_broker
        self.config_data = config_data

    def call_builtins(self, name):
        try:
            getattr(self, name)()
        except AttributeError as e:
            obj = str(e)[-(len(name)+1):-1]
            if obj != name:
                input('Attribute Error: ' + str(e))
                getattr(self, name)()

    def call_events(self):

        for event in self.event_handler.events:
            if event[1](*event[2]):
                event[0]()


    def register(self, func, cond, args=[]):
        self.event_handler.add(func, cond, args)

    def shutdown(self, call_end=True, force=True):
        self.alg_stat = 'disconnect'
        if call_end:
            self.call_builtins('end')
        if force:
            raise Disconnected("Disconnected.")
        return "disconnect"

    def pause(self):
        self.alg_stat = 'paused'
        return 'Paused'

    def resume(self):
        self.alg_stat = 'running'
        return 'Resumed'

    def empty(self):
        self.broker.cancel_all('BUY')
        self.broker.cancel_all('SELL')
        self.broker.sell('MARKET', self.broker.get_position()['free'])
        return 'Sold'

    def save_globals(self):
        Globals.set(self.symbol, self.globals)
        Globals.save(self.fm)

    def set_globals(self, save=False):
        Globals.set(self.symbol, self.globals)
        if save:
            Globals.save(self.fm)

    def load_globals(self, path):
        data = self.fm.load(path)
        if self.symbol in data:
            return data[self.symbol]

    def bind(self, alg, auto=False):
        alg.setup(self.broker, self.fm, master=self, auto_broker=auto)
        return alg

class Alarm:
    """This is a class that can be used to trigger functions in different intervals."""
    statics = {}

    def __init__(self, broker, interval, delta=None):
        """Constructor method
        :param broker: Broker object
        :param interval: The interval in which the target function should be triggered. Units: (seconds: s, minutes: m, days: d, weeks: w, years: y.
        :type interval: string
        :param delta: Amount of delay to add on each interval. eg. interval of "1w" with delta=timedelta(days=3) would mean "every Wednesday".
        :type delta: datetime.Timedelta
        """
        self.intervals = {'1w': [7, 'D'], '1d': [1, 'D'],
                        '1h': [1, 'h'], '30m': [30, 'm'], '15m': [15, 'm'], '1m': [1, 'm'], '1s': [1, 's']}

        self.interval = interval
        if interval.lower() in self.intervals.keys():
            self.args = self.intervals[interval.lower()]
        else:
            err('No such interval for an alarm')
            self.args = None
        self.delta = delta
        self.broker = broker
        self.time_buffer = self.broker.get_time()

    def __call__(self):
        """Will return true if the current interval has ended."""
        time = self.broker.get_time()
        cur_floor = datetime.timestamp(Alarm._floor(time, self.interval, self.delta))
        last_floor = datetime.timestamp(Alarm._floor(self.time_buffer, self.interval, self.delta))
        cond = cur_floor != last_floor
        self.time_buffer = time
        return cond

    def static(broker, interval, id, delta=None):
        """Alternative constructor that will keep track of the interval staticly."""
        if id not in Alarm.statics.keys():
            Alarm.statics[id] = Alarm(broker, interval, delta)

        return Alarm.statics[id]

    def _floor(date, interval, delta=None):
        if delta != None:
            delta = delta.total_seconds()
        else:
            delta = 0
        date = date.timestamp()
        units = {'w': (604800, 345600), 'd': (86400, 0),
                 'h': (3600, 0), 'm': (60, 0), 's': (1, 0)}
        freq = int(''.join([i for i in interval if i.isdigit()]))
        unit = ''.join([i for i in interval if i.isalpha()])
        coef = units[unit][0] * freq
        delt = units[unit][1] + delta

        result = (date - delt) - ((date - delt) % coef) + delt
        return datetime.fromtimestamp(int(result))

class Broker_Debug:
    def __init__(self, broker):
        self.broker = broker

    def get_report(self, interval='15m'):
        bal = self.broker.get_balance()
        pos = self.broker.get_position()
        orders = self.orders_clean()
        #d = binance.delta()

        market = '\n'.join(['MARKET',
                            f'price: {self.broker.get_price()}',
                            f'ohlc: {self.broker.get_ohlc(interval)}',
                            f'best_bid: {self.broker.get_sell_price()}',
                            f'best_ask: {self.broker.get_buy_price()}',
                            f'time: {self.broker.get_time()}'])

        balance = '\n'.join(['RESERVED BALANCE',
                             f'full: {bal["full"]}',
                             f'free: {bal["free"]}',
                             f'locked: {bal["locked"]}'])

        position = '\n'.join(['POSITION',
                              f'full: {pos["full"]}',
                              f'free: {pos["free"]}',
                              f'locked: {pos["locked"]}'])

        open_buys = '\n'.join(['OPEN ORDERS (BUY)'] + orders[0])
        open_sells = '\n'.join(['OPEN ORDERS (SELL)'] + orders[1])

        #system = '\n'.join(['SYSTEM', f'ping {d[0]}', f'delta {d[1]}'])

        msg = '\n\n'.join(['\n'] + [market] + [open_buys] +
                          [open_sells] + [balance] + [position])
        return msg

    def get_report_sheets(self, interval):

        bal = self.broker.get_balance()
        pos = self.broker.get_position()
        orders = self.orders_clean()

        market = [['MARKET', ''],
                  ['price:', self.broker.get_price()],
                  ['best_bid:', self.broker.get_sell_price()],
                  ['best_ask:', self.broker.get_buy_price()],
                  ['time:', str(self.broker.get_time())]]

        balance = [['RESERVED BALANCE', ''],
                   ['full:', bal["full"]],
                   ['free:', bal["free"]],
                   ['locked:', bal["locked"]]]

        position = [['POSITION', ''],
                    ['full:', pos["full"]],
                    ['free:', pos["free"]],
                    ['locked:', pos["locked"]]]

        open_buys = [['OPEN ORDERS (BUY)', '']] + [['', ord]
                                                   for ord in orders[0]]
        open_sells = [['OPEN ORDERS (SELL)', '']] + [['', ord]
                                                     for ord in orders[1]]

        #system = '\n'.join(['SYSTEM', f'ping {d[0]}', f'delta {d[1]}'])

        msg = market + open_buys + open_sells + \
            balance + position + ([['', '']] * 20)
        return msg

    def take_action(self):
        action = input('>>')
        if action == 'buy':
            self.broker.buy('MARKET', 2)
        if action == 'sell':
            self.broker.sell('MARKET', 2)
        if action == 'lbuy':
            self.broker.buy('LIMIT', 2, 7.0081)
        if action == 'lsell':
            self.broker.sell('LIMIT', 2, 7.0138)
        if action == 'cancelbuy':
            self.broker.cancel_all('BUY')
        if action == 'cancelsell':
            self.broker.cancel_all('SELL')

    def orders_clean(self):
        buys = self.broker.get_open_orders()['BUY']
        sells = self.broker.get_open_orders()['SELL']
        buys = ['#' + str(ord['orderId']) + '\t' + str(ord['origQty']
                                                       ) + '\t' + str(ord['price']) for ord in buys]
        sells = ['#' + str(ord['orderId']) + '\t' + str(ord['origQty']
                                                        ) + '\t' + str(ord['price']) for ord in sells]

        return (buys, sells)

class Trail:
    """This class can be used to create trailling loss orders"""
    def __init__(self, broker, perc, save=False):
        """Constructor
        :param broker: broker object
        :param perc: The trailling percentage (0.0-1.0)
        :param save: Whether to save the trail loss in a list for plotting:
        """
        self.perc = perc
        self.broker = broker
        self.locked = False
        self.trail = -1
        self.last_trail = -1
        self.active = False
        self.dir = 1 if perc>1.0 else -1
        self.hist = {}
        self.save = save
    def __call__(self):
        """This object must be called whenever the trail must be updated with the new price"""
        price = self.broker.get_price()
        if not self.locked and (price * self.perc) * self.dir <= self.trail * self.dir:
            self.last_trail = self.trail
            self.trail = price * self.perc
        if self.save:
            self.hist[self.broker.get_timestamp()] = {"trail": self.trail, "locked": self.locked, "active": self.active} 

    def reset(self, target_price=None):
        """Resets the trail to the current price * perc
        :param target_price: float (Optional)
        """
        if target_price == None:
            self.trail = self.broker.get_price() * self.perc
        else:
            self.trail = target_price * self.perc

        self.last_trail = -1

    def on_change(self, dir):
        """Returns True if trails last movement is in the same direction as <dir>/
        :param dir: "higher", or "lower",
        :type dir: string
        """
        cond1 = self.last_trail != -1
        cond2 = dir == 'higher' and self.trail > self.last_trail
        cond3 = dir == 'lower' and self.trail < self.last_trail

        return not self.locked and cond1 and (cond2 or cond3)

    def on_hit(self):
        """Returns true if the price hit the trail"""
        return self.active and self.broker.get_price() <= self.trail

class Traces:
    def __init__(self, broker):
        self.traces = {}
        self.labels = {}
        self.broker = broker
        self.region = None
        self.__changed = False
        self.hist = {}
        self.crossed_at = -1


    def __call__(self):
        price = self.broker.get_price()
        region = None
        size = len(self.traces.keys())
        for i, v in enumerate(self.traces.values()):
            region = size - round((size) / 2)
            if price < v:
                region = i - round(size / 2)
                break

        self.__changed = self.region != None and region != self.region
        if self.__changed:
            self.crossed_at = self.broker.get_timestamp()
        self.region = region

    def here_since (self, region, duration):
        return region == self.region and self.broker.get_timestamp() >= self.crossed_at + duration

    def set_traces(self, new_traces, save=None):
        self.traces = dict(sorted(new_traces.items(), key=lambda x: x[1]))
        if save != None:
            self.hist[save] = list(new_traces.values())

    def get_traces(self):
        return self.traces

    def get_region(self):
        return self.region

    def is_inside(self, region, ohlc):
        r = region + int(len(self.traces.keys()) / 2)
        s = region + int(len(self.traces.keys()) / 2) - 1
        for kline in ohlc:
            cond1 = r == len(self.traces) or list(
                self.traces.values())[r] > kline['high']
            cond2 = s == -1 or list(self.traces.values())[s] < kline['low']
            if not (cond1 and cond2):
                return False
        return True

    def on_change(self, region=None):
        if region == None:
            region = self.region
        return self.__changed and self.region == region

class Plot:

    def browser(ohlc, traces=None, trades= None, **kwargs):

        k = pd.DataFrame(ohlc)
        k['time'] = pd.to_datetime(k["time"], unit='s')

        fig = go.Figure(data=[go.Candlestick(x=k['time'], open=k['open'], high=k['high'], low=k['low'], close=k['close'])])

        if trades != None:
            start = k.iloc[-1]['time'].timestamp()
            trades = [trd for trd in trades if trd['time'] > start]
            buys = [trd for trd in trades if trd['side'] == 'BUY']
            sells = [trd for trd in trades if trd['side'] == 'SELL']
            fig.add_trace(go.Scatter(x=[datetime.fromtimestamp(trd['time'], tz=tz.tzutc())
                                        for trd in buys], y=[trd['price'] for trd in buys], mode='markers', marker_size=8, marker_line_width=2, marker_color='red', name='Bought'))
            fig.add_trace(go.Scatter(x=[datetime.fromtimestamp(trd['time'], tz=tz.tzutc())
                                        for trd in sells], y=[trd['price'] for trd in sells], mode='markers', marker_size=8, marker_line_width=2, marker_color='green', name='Sold'))


        if traces != None:
            k = Plot.__merge_traces(k, traces)
            traced = k.loc[k['T1'] != 0]

            fig.add_trace(go.Scatter(x=traced['time'], y=traced['T1'],
                                    line=dict(color='red', dash='dot', width=1)))
            fig.add_trace(go.Scatter(x=traced['time'], y=traced['T2'],
                                    line=dict(color='red', dash='dot', width=1)))
            fig.add_trace(go.Scatter(x=traced['time'], y=traced['T3'],
                                    line=dict(color='green', dash='dot', width=1)))
            fig.add_trace(go.Scatter(x=traced['time'], y=traced['T4'],
                                    line=dict(color='green', dash='dot', width=1)))
        
        for val in kwargs.values():
            val['time'] = pd.to_datetime(val['time'], unit='s')
            fig.add_trace(go.Scatter(x=val['time'], y=val['value']))

        fig.update_yaxes(fixedrange=False)
        fig.show()


    def html(ohlc, traces, trades, fm, name):

        k = pd.DataFrame(ohlc)

        k['time'] = pd.to_datetime(k["time"], unit='s')
        fig = go.Figure(data=[go.Candlestick(
            x=k['time'], open=k['open'], high=k['high'], low=k['low'], close=k['close'])])

        if trades != None:
            start = k.iloc[-1]['time'].timestamp()
            trades = [trd for trd in trades if trd['time'] > start]
            buys = [trd for trd in trades if trd['side'] == 'BUY']
            sells = [trd for trd in trades if trd['side'] == 'SELL']
            fig.add_trace(go.Scatter(x=[datetime.fromtimestamp(trd['time'], tz=tz.tzutc())
                                        for trd in buys], y=[trd['price'] for trd in buys], mode='markers', marker_size=8, marker_line_width=2, marker_color='red', name='Bought'))
            fig.add_trace(go.Scatter(x=[datetime.fromtimestamp(trd['time'], tz=tz.tzutc())
                                        for trd in sells], y=[trd['price'] for trd in sells], mode='markers', marker_size=8, marker_line_width=2, marker_color='green', name='Sold'))

        if traces != None:
            k = Plot.__merge_traces(k, traces)
            traced = k.loc[k['T1'] != 0]

            fig.add_trace(go.Scatter(x=traced['time'], y=traced['T1'],
                                     line=dict(color='red', dash='dot', width=1)))
            fig.add_trace(go.Scatter(x=traced['time'], y=traced['T2'],
                                     line=dict(color='red', dash='dot', width=1)))
            fig.add_trace(go.Scatter(x=traced['time'], y=traced['T3'],
                                     line=dict(color='green', dash='dot', width=1)))
            fig.add_trace(go.Scatter(x=traced['time'], y=traced['T4'],
                                     line=dict(color='green', dash='dot', width=1)))
        fig.write_html(fm.dir['graph'] + name.lower() + '.html')


    def __trace_match(x, traces):
        if x.timestamp() in traces.keys():
            return traces[x.timestamp()]
        else:
            return [0, 0, 0, 0]

    def __merge_traces(df, traces):
        floored = (df['time'] - df['time'].dt.weekday.astype('timedelta64[D]')).dt.floor('1D')
        tdf = floored.apply(Plot.__trace_match, args=[traces])
        tdf = tdf.apply(pd.Series).rename(
            columns=lambda x: ['T1', 'T2', 'T3', 'T4'][x])
        return pd.concat([df, tdf], axis=1)

class Sock:

    __queries = {}
    __enabled = False
    __port = 3003
    __n = 5

    def add(query, func):
        if query != Sock.__queries.keys():
            Sock.__queries[query] = [func]
        elif func not in Sock.__queries[query]:
            Sock.__queries[query].append(func)
        else:
            return 'Already exist!'

        if not Sock.__enabled:
            listener = threading.Thread(target=Sock.__launch)
            listener.start()

    def send(msg, timeout=5.0, port=None):
        try:
            if port == None:
                port = Sock.__port
            s = socket.socket()
            s.connect(('127.0.0.1', port))
            s.settimeout(timeout)
            resp = s.recv(1024)
            s.close()
            return resp.decode()
        except socket.timeout as e:
            print(e)


    def __launch():
        Sock.__enabled = True
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('', Sock.__port))
        s.listen(Sock.__n)

        while Sock.__enabled:
            c, addr = s.accept()
            threading.Thread(target=Sock.__respond, args=(c, addr)).start()

    def __respond(c, addr):

        data = c.recv(1024).decode()

        if data == '/kill':
            Sock.__enabled = False

        elif data in Sock.__queries.keys():
            resp = [func() for func in Sock.__queries[data]][0]
            c.send(resp.encode())
            time.sleep(0.1)

class Globals:
    variables = {}

    def get(key, parent=None):
        try:
            if parent == None:
                return Globals.variables[key]
            else:
                return Globals.variables[parent][key]
        except Exception as a:
            print('runtime_errors', 'Globals.get key error: ' + str(a))

    def set(key, var, parent=None):
        try:
            if parent == None:
                Globals.variables[key] = var
            else:
                if parent not in Globals.variables.keys():
                    Globals.variables[parent] = {}
                Globals.variables[parent][key] = var
        except Exception as a:
            print('runtime_errors', 'Globals.set key error: ' + str(a))

    def save(fm):
        fm.save(Globals.variables, 'globals')

class Tools:
    def pretty_print(var, sort_keys=False, indent=4):
        lines = json.dumps(var, sort_keys=sort_keys, indent=indent).splitlines()
        output = []
        for line in lines:
            line = line.replace('[', '')
            line = line.replace(']', '')
            line = line.replace('(', '')
            line = line.replace(')', '')
            line = line.replace('{', '')
            line = line.replace('}', '')
            if line.replace('\t', '').replace(',', '').replace(' ', '') != '':
                output.append(line)
        return '\n'.join(output)

class Slack:

    def __init__ (self, token, default_channel=None):
        self.token = token
        self.default_channel = default_channel

    def send (self, msg, channel=None):

        if channel == None:
            channel = self.default_channel

        #C03FSGFMA5B
        headers = {'Authorization': 'Bearer ' + self.token}
        uri = 'https://slack.com/api/chat.postMessage'
        data = {"channel": channel, "text": msg}
        resp = requests.post(uri, json=data, headers=headers).json()
        return(resp)

class Sheets:
    def __init__(self, conf, sh):
        self.sa = gspread.service_account(filename=conf)
        self.sh = self.sa.open(sh)

    def set_trades(self, trades, sheet):
        df = self.__pull_trades(trades)
        arr = [df.columns.values.tolist()] + df.values.tolist()
        wks = self.sh.worksheet(sheet)
        wks.update(arr)

    def __pull_trades(self, trd, n=90):
        df = pd.DataFrame(trd)
        df["time"] = pd.to_datetime(df["time"], unit='ms')
        df.set_index('time', inplace=True)
        df.sort_index(inplace=True)
        df = df[::-1]
        df = df[df.index > datetime.now() - timedelta(days=n)]
        df = df[df.index > datetime(2022, 6, 25)].reset_index()

        df['time'] = df['time'].values.astype(np.int64) // 10 ** 9
        df = df[['orderId', 'time', 'symbol', 'price', 'qty', 'quoteQty',
                 'commission', 'commissionAsset', 'isBuyer', 'isMaker']]
        return df

    def days_filter(df, n):
        return df[df.index > datetime.datetime.now() - datetime.timedelta(days=n)]
