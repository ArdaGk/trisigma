from .alg_exceptions import Disconnected
from .alg_events import BaseListener
from .toolkit import Sock

class Strategy:
    shared_data = {"symbols": {}}
    __label = None
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

    def setup(self, broker, fm, master=None, auto_broker = True, config_data = {}, label = "unlabeled"):
        self.alg_stat = 'init'
        self.label = label
        Strategy.label = label
        self.stats = {}
        self.event_handler = BaseListener()
        self.broker = broker
        self.symbol = broker.symbol
        self.globals = {}
        self.fm = fm
        self.master = master
        self.auto_broker = auto_broker
        self.config_data = config_data
        Strategy.shared_data[broker.symbol] = {}
        Sock.add(self.symbol + " pause", self.pause)
        Sock.add(self.symbol + " resume", self.resume)
        Sock.add(self.symbol + " sellall", self.empty)
        Sock.add(self.symbol + " hello", lambda: "Hi")
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
        self.empty()
        return f'{self.symbol} paused, assets are sold and open orders are canceled.'

    def resume(self):
        self.alg_stat = 'running'
        return f'{self.symbol} bot can now trade.'

    def empty(self):
        self.broker.cancel_all()
        self.broker.cancel_all()
        self.broker.sell('MARKET', self.broker.get_position()['free'])
        return f'{self.symbol}s sold'

    def save_shared_data(self):
        self.fm.save(Strategy.shared_data, f'{Strategy.__label}_shared_data')

    def load_shared_data(self):
        data = self.fm.load(f'{Strategy.__label}_shared_data')
        return data

    def get_shared_data(self):
        return Strategy.shared_data

    def bind(self, alg, auto=False):
        alg.setup(self.broker, self.fm, master=self, auto_broker=auto)
        return alg

