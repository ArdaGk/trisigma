from trisigma import *


class Alg (Algorithm):

    def start (self):
        self.lines_printed = 0
        self.globals['price'] = self.broker.get_price()
        self.globals['position'] = self.broker.get_position()
        self.globals['open_orders'] = self.broker.get_open_orders()
        self.globals['trades_len'] = len(self.broker.get_trades())
        self.set_globals()
     
    def update (self):
        pass
    def late_update (self):
        self.globals['price'] = self.broker.get_price()
        self.globals['position'] = self.broker.get_position()
        self.globals['open_orders'] = self.broker.get_open_orders()
        self.globals['trades_len'] = len(self.broker.get_trades())
        self.set_globals()
        if self.broker.symbol == 'LINKUSDT':
            self.display()

    def display (self):
        line = '\n' + ('='*30) + '\n'
        frames = [f"=========== REPORT ===========\nDate:\t\t{self.broker.get_time()}\nBalance:\t${self.broker.get_balance()['full']}"]
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
                pass
        plain = line.join(frames)
        lns = len(plain.splitlines())
        if self.lines_printed == 0:
            self.lines_printed = lns
            output = plain
        else:
            UP = f"\x1B[{self.lines_printed+1}A"
            CLR = "\x1B[0K"
            output = UP + plain.replace('\n', CLR+"\n")
            self.lines_printed = lns
        print(self.lines_printed + f"/{len(output.splitlines())}")
