from datetime import datetime, timedelta
from . import binance_stream
from . import ibkr
from . import webull
import time
import threading
from trisigma.filemanager import FileManager
from trisigma import Sock

class LiveTest:
    """This is the class that will connect a Strategy object to a brokerage firm"""
    def __init__(self, conf=None, **kwargs):
        """Constructor for LiveTest

        :param conf: config details for the live test.
        :type conf: <dict>
        """
        conf = conf | kwargs
        self.symbols = conf['symbols']
        #self.intervals = conf['intervals']
        self.main = conf['freq']
        self.alg = conf['alg']
        self.load = conf['load']
        self.fm = FileManager() if 'fm' not in conf.keys() else FileManager(conf['fm'])
        self.platform = conf['platform']
        self.end_time = 10**12 if "end_time" not in conf.keys() else conf['end_time']
        self.label = conf['label']
        self.freq = conf['freq']

        if self.platform.lower() in ["binance", "binance.com"]:
            self.api_key = conf["api_key"]
            self.secret_key = conf["secret_key"]
            self.setup = self.__binance_setup
        elif self.platform.lower() in ["ibkr-real", "ib-real", "ibkr-paper", "ib-paper"]:
            self.setup = self.__ibkr_setup
            ports = {'TWS': {'LIVE': 7496, 'PAPER': 7497},
                    'IBG': {'LIVE': 4001, 'PAPER': 4002}}
            self.port = ports['TWS'][self.platform.split('-')[1].upper()]
        elif self.platform.lower() in ['webull-paper', 'webull-real']
            self.setup = self.__webull_setup
            self.cred = conf['credentials']

    def connect(self, *argv):
        """Starts the live test. This function will require additional arguments depending on the platform of choice"""
        #Some initial setup
        self.setup(*argv)

        #Start both client and Bot Controller
        self.start()

    def __binance_setup(self, *argv):
        self.client = binance_stream.Client(self.api_key, self.secret_key, [sym['symbol'] for sym in self.symbols], self.fm, label=self.label)
        self.wait = 1
        self.init = (datetime.now() - timedelta(days=1)).timestamp()
        self.resps = {}
        self.bots = {}
        for sym in self.symbols:
            self.bots[sym['symbol']] = {"alg": self.alg(), "freq": sym['freq'], "last": datetime.now().timestamp()}
            self.bots[sym['symbol']]['alg'].setup(binance_stream.Broker(sym['symbol'], sym['balance'], self.client), self.fm, config_data=sym, label = self.label)
            for k, v in self.load.items():
              self.client.update_klines(sym['symbol'], k, v)
        Sock.add("pause", self.pause)
        Sock.add("resume", self.resume)

    def __ibkr_setup(self, *argv):
        self.client = ibkr.Client()
        time.sleep(1)
        self.client.connect(argv[0], self.port, 456)
        time.sleep(1)
        self.client_thread = threading.Thread(target=self.client.run, daemon=True)
        self.client_thread.start()
        self.wait = 0.1
        self.client.setup([sym['symbol'] for sym in self.symbols])
        self.init = (datetime.now() - timedelta(days=1)).timestamp()
        self.resps = {}
        self.bots = {}
        for sym in self.symbols:
            self.bots[sym['symbol']] = {"alg": self.alg(), "freq": sym['freq'], "last": datetime.now().timestamp()}
            self.bots[sym['symbol']]['alg'].setup(ibkr.Broker(sym['symbol'], -1, self.client), self.fm, config_data=sym)
            #self.bots[sym['symbol']]['alg']
            for k, v in self.load.items():
                self.client.load_ohlc(sym['symbol'], v, k)

    def __webull_setup(self, *argv):
        self.client = webull.Client(self.cred, self.label, self.fm)
        self.wait = 1
        self.init = (datetime.now() - timedelta(days=1)).timestamp()
        self.resps = {}
        self.bots = {}
        for sym in self.symbols:
            self.bots[sym['symbol']] = {"alg": self.alg(), "freq": self.freq, "last": datetime.now().timestamp()}
            self.bots[sym['symbol']]['alg'].setup(webull.Broker(sym['symbol'], self.client), self.fm, config_data=sym, label = self.label)
        Sock.add("pause", self.pause)
        Sock.add("resume", self.resume)


    def start(self):
        while datetime.now().timestamp() < self.end_time:
            try:
                time.sleep(self.wait)
                ready_bots = self.pick()
                if ready_bots:
                    self.client.generic_update()
                self.update(ready_bots)
                self.fire(ready_bots)
                self.evaluate()
            except Exception as e:
                raise e
        print("Stream Ended")

    def pick(self):
        return dict(list(filter(lambda item: self.__is_ready(item[1]), self.bots.items())))

    def update(self, bots):
        pass

    def fire(self, bots):
        for k, v in bots.items():
            try:
                v['last'] = datetime.now().timestamp()
                v['alg']()
                v['freq'] = v['alg'].config_data['freq']
                self.resps[k] = v
            except ConnectionResetError as exc:
                print(exc)

    def evaluate(self):
        pass

    def pause (self):
        resp = []
        for bot in self.bots.values():
            resp.append(bot['alg'].pause())
        print("stream paused")
        return '\n'.join(resp)

    def resume (self):
        resp = []
        for bot in self.bots.values():
            resp.append(bot['alg'].resume())
        print("stream resumed")
        return '\n'.join(resp)

    def __is_ready(self, bot):
        now = datetime.now().timestamp()
        last_dur = bot['last'] - self.init
        cur_dur = now - self.init
        output = self.__floor(last_dur, bot['freq']) != self.__floor(
            cur_dur, bot['freq'])
        return output

    def __floor(self, date, interval, delta=None):
        if delta != None:
            delta = delta.total_seconds()
        else:
            delta = 0
        if not isinstance(date, (int, float)):
            date = date.timestamp()
        units = {'w': (604800, 345600), 'd': (86400, 0),
                 'h': (3600, 0), 'm': (60, 0), 's': (1, 0)}
        freq = int(''.join([i for i in interval if i.isdigit()]))
        unit = ''.join([i for i in interval if i.isalpha()])
        coef = units[unit][0] * freq
        delt = units[unit][1] + delta

        result = (date - delt) - ((date - delt) % coef) + delt
        return datetime.fromtimestamp(int(result))
