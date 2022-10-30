from trisigma import *


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
        self.set_globals()
        self.display()

    def display (self):
        line = '\n' + ('='*30) + '\n'
        frames = [f"=========== REPORT ============\nDate:\t{self.broker.get_time()}\nBalance:\t${self.broker.get_balance()['full']}"]
        for k, v in Globals.variables.items():
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
        output = line.join(frames)
        UP = '\033[1A'
        CLEAR = '\x1b[2K'

        print(UP,end=CLEAR)
        print(output)
