from datetime import datetime, timedelta
from . import binance_stream
from . import ibkr
from . import webull
import time
from .time_utils import to_timestamp
import threading
from trisigma.filemanager import FileManager
from trisigma import Sock
#Won't work with binance because of seperate balancing


class LiveTest:
    """This is the class that will connect a Strategy object to a brokerage firm"""
    def __init__(self, conf=None, **kwargs):
        """Constructor for LiveTest

        :param conf: config details for the live test.
        :type conf: <dict>
        """
        conf = conf | kwargs
        self.load = conf['load']
        self.fm = FileManager() if 'fm' not in conf.keys() else FileManager(conf['fm'])
        self.platform = conf['platform']
        self.end_time = 10**12 if "end_time" not in conf.keys() else conf['end_time']

        self.client = self.__get_client(conf)
        self.algos = self.__build_algos(conf['strategy'], self.client, conf['symbols'], conf['label'], conf['freq'], conf['fm'])

    def connect(self, *argv):
        """Starts the live test. This function will require additional arguments depending on the platform of choice"""
        while datetime.now().timestamp() < self.end_time:
            try:
                time.sleep(0.3)
                [algo.fire() for algo in self.algos]
            except ConnectionError as e:
                self.fm.log("connection", "Connection Error")
        print("Stream Ended")

    def __get_client(self, conf):
        platform = conf['platform']
        symbols = [sym_data['symbol'] for sym_data in conf['symbols']]
        if platform in ['binance']:
            return binance_stream.Client(conf['api_key'], conf['secret_key'], symbols, self.fm, conf['label'])
        elif platform in ['webull-paper']:
            return webull.Client(conf['credentials'], conf['load'], symbols, self.fm , conf['label'])

    def __get_broker(self):
        if self.platform in ['binance']:
            return binance_stream.Broker
        elif self.platform in ['webull-paper', 'webull-real']:
            return webull.Broker

    def __build_algos (self, strategy, client, symbols, label, main_freq, fm):
        algos = []
        for sym_data in symbols:
            freq = main_freq if "freq" not in sym_data.keys() else sym_data['freq']
            broker = self.__get_broker()(sym_data['symbol'], client)
            algo = MonoAlgo(strategy, broker, fm, sym_data, label, freq)
            algos.append(algo)
        return algos

        
    def pause (self):
        resp = []
        for algo in self.algos:
            resp.append(algo.get_algo().pause())
        print("stream paused")
        return '\n'.join(resp)

    def resume (self):
        resp = []
        for algo in self.algos:
            resp.append(algo.get_algo().resume())
        print("stream resumed")
        return '\n'.join(resp)


class MonoAlgo:
    def __init__ (self, algo, broker,fm, config_data, label, freq):
        self.algo = algo()
        self.algo.setup(broker, fm, config_data=config_data, label=label)
        self.freq = to_timestamp(freq)
        self.last_fire = -1
    def fire (self):
        now = datetime.now().timestamp()
        elapsed = now - self.last_fire
        if elapsed >= self.freq:
            self.algo()
            self.last_fire = now

    def get_algo(self):
        return self.algo

