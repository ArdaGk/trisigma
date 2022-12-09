import json
import time
import re
import socket
import threading
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from dateutil import tz
from .alg_exceptions import Disconnected, AlgException, err
from .alg_events import BaseListener
import requests
import gspread
import numpy as np


class Alarm:
    """This is a class that can be used to trigger functions in different intervals."""
    statics = {}

    def __init__(self, broker, interval, delta=None):
        """Constructor method

        :param broker: Broker object
        :type broker: trisigma.Broker
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

    def static(broker, interval, _id, delta=None):
        """Alternative constructor that  will keep track of the interval staticly.

        :param broker: Broker object
        :type broker: trisigma.Broker
        :param interval: The interval in which the target function should be triggered. Units: (seconds: s, minutes: m, days: d, weeks: w, years: y.
        :type interval: string
        :param _id: identifier for the alarm. If an id for the alarm already exist, then that alarm will be returned.
        :type _id: string
        :param delta: Amount of delay to add on each interval. eg. interval of "1w" with delta=timedelta(days=3) would mean "every Wednesday".
        :type delta: datetime.Timedelta
        """ 
        if _id not in Alarm.statics.keys():
            Alarm.statics[_id] = Alarm(broker, interval, delta)

        return Alarm.statics[_id]

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

class Trail:
    """This class can be used to create trailling loss orders"""
    def __init__(self, broker, perc, save=False):
        """Constructor for Trail object

        :param broker: broker objecttool
        :type broker: trisigma.Broker
        :param perc: The trailling percentage (0.0-1.0)
        :type perc: int
        :param save: Whether to save the trail in a list for plotting:
        :type save: bool
        """
        self.perc = perc
        self.broker = broker
        self.locked = False
        self.trail = -1
        self.last_trail = -1
        self.active = False
        self.dir = 1 if perc>0 else -1
        self.hist = {}
        self.save = save
        self.is_active = lambda: self.active
        self.is_locked = lambda: self.locked
    def __call__(self):
        """This object must be called in order to update the trail based on the new price"""
        if self.active:
            if not self.locked:
                price = self.broker.get_price()
                cond1 = price * self.perc * self.dir < self.trail * self.dir
                cond2 = self.trail == -1
                if cond1 or cond2:
                    self.last_trail = self.trail
                    self.trail = price * self.perc
        else:
            self.trail = -1
        if self.save:
            self.hist[self.broker.get_timestamp()] = {"trail": self.trail, "locked": self.locked, "active": self.active}
        return
        if not self.locked and (price * self.perc) * self.dir <= self.trail * self.dir:
            self.last_trail = self.trail
            self.trail = price * self.perc
        if self.save:
            self.hist[self.broker.get_timestamp()] = {"trail": self.trail, "locked": self.locked, "active": self.active}

    def reset(self, target_price=None):
        """Resets the trail to the current price * perc

        :param target_price: resets to target_price*perc instead of current_price*perc
        :type target_price: float
        """
        perc = self.perc
        if target_price == None:
            self.trail = self.broker.get_price() * perc
        else:
            self.trail = target_price * perc

        self.last_trail = -1

    def is_active(self):
        """Returns true of trail is active"""
        return self.active

    def set_perc(self, perc):
        self.perc = perc

    def set_peak (self, peak):
        self.last_trail = self.trail
        self.trail = peak * self.perc

    def lock(self, value=None):
        """When locked, trail will remain the same even if price changes.

        :param value: lockes the trail at a specific value.
        :type value: float
        """
        self.locked = True
        if value != None:
            self.trail = value

    def unlock(self):
        """When unlocked, trail will be reset to its original value. Trail value will change as price goes beyond the percentage."""
        self.locked=False

    def on_change(self, _dir): #Obsolete
        """Returns True if trails last movement is in the same direction as <dir>

        :param dir: "higher", or "lower",
        :type dir: string
        """
        cond1 = self.last_trail != -1
        cond2 = _dir == 'higher' and self.trail > self.last_trail
        cond3 = _dir == 'lower' and self.trail < self.last_trail

        return not self.locked and cond1 and (cond2 or cond3)

    def on_hit(self):
        """Returns true if the price hit the trail"""
        return self.active and self.broker.get_price() <= self.trail

    def activate(self):
        """Activates the trail. When activated, trigger functions like on_hit() will be usable."""
        self.active = True
        self()
    def deactivate(self):
        """Deactivates the trail. When deactivated, trigger functions like on_hit will always return False."""
        self.active = False
        self()
class Traces:
    """This class can be used to set regions defined by traces"""
    def __init__(self, broker):
        """Constructor for Traces object"""
        self.traces = {}
        self.labels = {}
        self.broker = broker
        self.region = None
        self.__changed = False
        self.hist = {}
        self.crossed_at = -1

    def __call__(self):
        """Calling this magic method will update the region of the current price based on the traces."""
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
        """Returns true if price been in the given reagon for a specified amount of time

        :param region: The region of the price
        :type region: int
        :param duration: How long, in seconds, is the price expected to be in this region?
        :type duration: int
        """
        return region == self.region and self.broker.get_timestamp() >= self.crossed_at + duration

    def set_traces(self, new_traces, save=None):
        """Set new traces

        :param new_traces: new traces as dict, key is the name value is the price point
        :type new_traces: dict
        """
        self.traces = dict(sorted(new_traces.items(), key=lambda x: x[1]))
        if save != None:
            self.hist[save] = list(new_traces.values())

    def get_traces(self):
        """Returns traces"""
        return self.traces

    def get_region(self):
        """Returns the region that the price is at """
        return self.region

    def is_inside(self, region, ohlc):
        """Checks wether if the price was inside the given region within the given candlesticks

        :param region: Region to check
        :type region: int
        :param ohlc: Candlesticks as a list of dict
        :type ohlc: dict[]
        """
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

class Sock:
    __queries = []
    __enabled = False
    __port = 3003
    __max_port = 10
    __n = 5
    __match = lambda msg, q: (q['re'] and re.search(q['query'], msg)) or (not q['re'] and q['query'] == msg)
    @staticmethod
    def add(query, func, re=False):
        """Adds a new function with a target query. Whenever the listener receives a new message that matches the query, it will call the given function.

        :param query: The message that will trigger the function.
        :type query: string
        :param func: The function that should be called whenever the proper message is received.
        :type func: function
        :param re: Enables regex search the query
        :type re: bool
        """
        entry = {"query": query, "func": func, "re":re}
        if entry not in Sock.__queries:
            Sock.__queries.append(entry)
        else:
            return 'Already exist!'

        if not Sock.__enabled:
            listener = threading.Thread(target=Sock.__launch)
            listener.start()
    @staticmethod
    def send(msg, timeout=5.0, port=None):
        """Sends a message in the socket

        :param msg: Content of the message
        :type msg: string
        :param timeout: timeout (default: 5.0)
        :type timeout: float
        :param port: the port to send a message from (default: 3003, this is the port that is used by the listener).
        :type port: int
        """
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

    @staticmethod
    def __launch():
        Sock.__enabled = True
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        for i in range(Sock.__max_port):
            try:
                Sock.__port+=1
                s.bind(('', Sock.__port))
            except OSError:
                continue
            break
        print("listening on port " + str(Sock.__port))
        s.listen(Sock.__n)
        while Sock.__enabled:
            c, addr = s.accept()
            threading.Thread(target=Sock.__respond, args=(c, addr)).start()

    def __respond(c, addr):
        data = c.recv(1024).decode()

        if data == '/kill':
            Sock.__enabled = False

        resp = [q['func'](data) for q in Sock.__queries if Sock.__match(data, q)]
        c.send(json.dumps(resp).encode())

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

class SocketMessenger:
    """Sends messages through local socket"""
    def __init__ (self, addr, port, timeout=10):
        """Constructor for Messenger
        :param addr: address eg. "127.0.0.1"
        :param port: 
        :param timeout: (Optional, default: 10), timeout in seconds
        :type timeout: <int>
        """
        self.addr = addr
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM);
        self.sock.connect((addr, port))
        self.sock.settimeout(timeout)

    def send (self, msg):
        """Sends the message
        :param msg: content of the message.
        """
        self.sock.send(msg.encode())
        resp = self.sock.recv(1024)
        return resp.decode()

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

