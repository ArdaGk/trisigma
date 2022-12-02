from trisigma import Strategy
from trisigma.toolkit import *
import os

class WebullTester (Strategy):

    def start (self):
        self.lines_printed = 0
        self.globals = {}
        self.globals['price'] = self.broker.get_price()
        self.globals['position'] = self.broker.get_position()
        self.globals['open_orders'] = self.broker.get_open_orders()
        self.globals['trades_len'] = len(self.broker.get_trades())
        Sock.add(f"{self.label} {self.broker.symbol}", self.action, re=True)

    def action (self, msg):
        try:
            parts = msg.lower().split()
            if parts[2].lower() == "cancel":
                print(self.broker.cancel_all())
                return
            typ  = parts[2]
            side = parts[3]
            amount = int(parts[4])
            limit = None if typ == "market" else int(parts[5])
            funcs = {"buy": self.broker.buy,
                    "quote_buy": self.broker.quote_buy,
                    "sell": self.broker.sell,
                    "quote_sell": self.broker.quote_sell}
            resp = funcs[side](typ.upper(), amount, limit_price=limit)
            return resp
        except Exception  as exc:
            print(exc)
            print(parts)


    def late_update (self):
        self.globals['price'] = self.broker.get_price()
        self.globals['position'] = self.broker.get_position()
        self.globals['open_orders'] = self.broker.get_open_orders()
        self.globals['trades_len'] = len(self.broker.get_trades())
        self.get_shared_data()[self.symbol] = self.globals
        self.display()

    def display (self):
        line = '\n' + ('='*30) + '\n'
        frames = [f"=========== REPORT ===========\nDate:\t\t{self.broker.get_time()}\nBalance:\t${self.broker.get_balance()['full']} ({self.broker.get_balance()['locked']})"]
        for k, v in self.get_shared_data().items():
            try:
                symbol = k
                price = v['price']
                pos = v['position']
                elements = [f"symbol:\t\t{k}",
                 f"price:\t\t{price}",
                 f"position:\t{pos['full']} ({pos['free']}+{pos['locked']})",
                 f"open buys:\t{len(v['open_orders']['BUY'])}",
                 f"open sells:\t{len(v['open_orders']['SELL'])}",
                 f"trades:\t\t{v['trades_len']}"]
                frame = '\n'.join(elements)
                frames.append(frame)
            except Exception as exc:
                print(exc)
        plain = line.join(frames)
        print(plain)
