from trisigma import *
from reporter import Reporter
from trisigma.stream import Stream
import os


class Alg (Algorithm):

    def start (self):
        pass
    def update (self):
        pass
    def late_update (self):
        self.globals['price'] = self.broker.get_price()
        self.globals['position'] = self.broker.get_position()
        self.globals['open_orders'] = self.broker.get_open_orders()
        self.globals['trades_len'] = len(self.broker.get_trades())

    def display (self):
        line = '='*25
        frames = []
        for k, v in Globals.items():
            try:
                symbol = k
                price = v['price']
                pos = v['position']
                elements = [f"symbol:\t{k}",
                 f"price:\t{price}",
                 f"position:\t{pos['full']} ({pos['free']}+{pos['locked']})",
                 f"open buys:\t{len(v['open_orders']['BUY'])}",
                 f"open sells:\t{len(v['open_orders']['SELL'])}",
                 f"trades:\t{v['trades_len']}"]
                frame = '\n'.join(elements)
                frames.append(frame)
            except Exception as exc:
                print(exc)
        output = line.join(frames)
        print(output)
