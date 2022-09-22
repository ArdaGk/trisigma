from unittest import result
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract, ContractDetails
from ibapi.order import *
from ibapi.execution import *
from datetime import datetime, timedelta
import threading
import time
from ibapi.ticktype import TickTypeEnum
from . import yahoo
from .scraper import Webull
from .time_utils import to_timestamp, to_timestamp_split
import json
import math


#Webull day limited to 23

class Broker:
    def __init__(self, symbol, balance, client):
        self.client = client
        self.symbol = symbol
        self.quote_asset = 'USD'
        self.start_balance = balance
        self.balance = balance
        self.position = 0
        self.open_orders = {'BUY': [], 'SELL': []}

    def __call__(self):
        self.client.get_trades()
        self.client.get_orders()
        self.client.load_price(self.symbol)
        self.client.get_position()
        self.client.get_acc_info()
        time.sleep(1)
        buys = list(filter(lambda x: x['side'] ==
                    'BUY', self.client.orders[self.symbol]))
        sells = list(
            filter(lambda x: x['side'] == 'SELL', self.client.orders[self.symbol]))
        self.open_orders = {'BUY': buys, 'SELL': sells}


        locked = sum([ord['price'] * ord['qty'] for ord in self.client.orders[self.symbol] if ord['side'] == 'SELL'])
        free = self.client.balance[self.symbol]
        self.position = {'full': free + locked, 'free': free, 'locked': locked}

        free = sum([trd['price'] * trd['qty'] * (-1 if trd['side'] == 'BUY' else 1) for trd in self.client.trades[self.symbol]]) + self.start_balance
        self.balance = {'full': free, 'free': free, 'locked': -1}

    def buy(self, _type, qty, limit_price=None):
        if _type in ['LIMIT', 'LMT']:
            self.client.trade(self.symbol, 'BUY', 'LMT', qty, limit_price)
        if _type in ['MARKET', 'MKT']:
            self.client.trade(self.symbol, 'BUY', 'MKT', qty)

    def quote_buy(self, _type, quote_price, limit_price=None):
        if _type in ['MARKET', 'MKT']:
            qty = int(quote_price / self.get_price())
            return self.buy('MARKET', qty)
        if _type in ['LIMIT', 'LMT']:
            qty = int(quote_price / limit_price)
            return self.buy('LIMIT', qty, limit_price)

    def sell(self, _type, qty, limit_price=None):
        if _type in ['LIMIT', 'LMT']:
            self.client.trade(self.symbol, 'SELL', 'LMT', qty, limit_price)
        if _type in ['MARKET', 'MKT']:
            self.client.trade(self.symbol, 'SELL', 'MKT', qty)

    def quote_sell(self, _type, quote_price, limit_price=None):
        if _type in ['MARKET', 'MKT']:
            qty = int(quote_price / self.get_price())
            return self.sell('MARKET', qty)
        if _type in ['LIMIT', 'LMT']:
            qty = int(quote_price / limit_price)
            return self.sell('LIMIT', qty, limit_price)

    def cancel(self, side, orderId):
        self.client.cancel(orderId)

    def cancel_all(self, side='all'):
        self.client.cancel_all(self.symbol, side)

    def get_open_orders(self):
        return self.open_orders

    def get_trades(self):
        return self.client.trades[self.symbol]

    def get_position(self):
        full = self.client.balance[self.symbol]
        return {'full': full, 'free': full, 'locked': full}

    def get_balance(self, reserved=True):
        full = self.client.balance[self.quote_asset]
        return {'full': full, 'free': full, 'locked': full}

    def get_ohlc(self, interval, lookback=1):
        return self.client.past_klines[self.symbol][interval][:lookback]

    def get_price(self, lookback=1):
        return self.client.quote[self.symbol]['price']

    def get_time(self, of_trade=False):
        return datetime.now()

    def get_timestamp(self, of_trade=False):
        return datetime.now().timestamp()

    def get_bids(self):
        return self.client.quote[self.symbol]['bid']

    def get_asks(self):
        return self.client.quote[self.symbol]['ask']

    def get_sell_price(self):
        return self.client.bids[self.symbol]

    def get_buy_price(self):
        return self.client.asks[self.symbol]

    def file_orders(self):
        pass

    def on_trade(self, side='all', _type='all'):
        pass


class Stream:
    def __init__(self, addr, user_id, client='TWS', acc='PAPER'):
        self.addr = addr
        self.user_id = user_id
        ports = {'TWS': {'LIVE': 7496, 'PAPER': 7497},
                 'TWS': {'LIVE': 4001, 'PAPER': 4002}}

        self.port = ports[client][acc]
        self.app = Client()

    def connect(self, alg, symbols, load, fm):

        #Some initial setup
        self.app.connect('127.0.0.1', 7497, 123)
        self.app_thread = threading.Thread(target=self.app.run, daemon=True)
        self.app_thread.start()
        self.wait = 0.1
        self.app.setup([sym['symbol'] for sym in symbols])
        self.init = (datetime.now() - timedelta(days=1)).timestamp()
        self.resps = {}
        self.bots = {}
        for sym in symbols:
            self.bots[sym['symbol']] = {
                "alg": alg(), "freq": sym['freq'], "last": datetime.now().timestamp()}
            self.bots[sym['symbol']]['alg'].setup(
                Broker(sym['symbol'], sym['balance'], self.app), fm, config_data=sym)
            self.bots[sym['symbol']]['alg']
            for k, v in load.items():
                self.app.load_ohlc(sym['symbol'],v,k)



        #Start both client and Bot Controller


        self.start()
        
    def start(self):

        while True:
            try:
                time.sleep(self.wait)
                ready_bots = self.filter()
                self.update(ready_bots)
                self.fire(ready_bots)
                self.evaluate()
            except Exception as e:
                raise e
                input(e)
                break

    def filter(self):
        return dict(list(filter(lambda item: self.__is_ready(item[1]), self.bots.items())))

    def update(self, bots):
        pass

    def fire(self, bots):
        for k, v in bots.items():

            v['last'] = datetime.now().timestamp()
            resp = v['alg']()
            self.resps[k] = v

    def evaluate(self):
        pass

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
                 'h': (3600, 0 ), 'm': (60, 0), 's': (1, 0)}
        freq = int(''.join([i for i in interval if i.isdigit()]))
        unit = ''.join([i for i in interval if i.isalpha()])
        coef = units[unit][0] * freq
        delt = units[unit][1] + delta

        result = (date - delt) - ((date - delt) % coef) + delt
        return datetime.fromtimestamp(int(result))




class Client (EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)


        self.quote = {}
        self.orders = {}
        self.trades = {}
        self.balance = {}
        self.past_klines = {}


        self.time = datetime.now()
        self.timestamp = self.time.timestamp()
        self.ticks = {}
        self.__last_id = 0
        self.entry_buffer = {}
        self.interval_buffer = {}
        self.req_buffer = {}
        self.open_reqs = []
        self.nextOrderId = 0
        self.init = 0
        self.exchange_info = {}
        self.contracts = {}
        self.acc_info = {}
        self.currency = 'USD'
        self.reqIds(-1)
        self.reqMarketDataType(3)
        self.get_acc_info()

    def timeit (self):
        print(time.time() - self.init, flush=True)
        self.init = time.time()

    def setup (self, symbols):
        for sym in symbols:
            self.balance[sym] = 0
            self.orders[sym] = []
            self.trades[sym] = []
            self.past_klines[sym] = {}
            self.contracts[sym] = self.contract(sym)

        self.update_exchange_info()
        self.get_orders()

    def get_position(self):
        self.reqPositions()

    def get_acc_info(self):
        self.reqAccountSummary(1001, 'All', f"$LEDGER:{self.currency}")

    def generic_update(self):
        pass

    def load_price(self, symbol):
        #quote = yahoo.get_quote(symbol)
        quote = {"bid": -1, "ask": -1, "price": Webull.get_price(symbol)}
        self.quote[symbol] = quote
        return quote

    def load_ohlc(self,symbol, range, interval):
        #Pull data
        now = datetime.now().timestamp()
        mins = round(to_timestamp(interval) / 60)
        days = math.ceil((mins * range) / 1440)
        if mins < 1440:
            df = Webull.get_klines_min([symbol], mins, days)
        else:
            df = Webull.get_klines_day(symbol)
        #df = yahoo.get_kline(symbol, start, now, interval)

        klines = list(reversed(json.loads(df.to_json(orient='records'))))

        #Save data
        units = {1: 's', 60: 'm', 3600: 'h', 86400: 'd', 604800: 'w', 31536000: 'y'}
        coef, unit = to_timestamp_split(interval)
        interval = f"{coef}{units[unit]}"

        if symbol in self.past_klines.keys():
            self.past_klines[symbol][interval] = klines

    def get_orders(self):
        for sym in self.orders.keys():
            self.orders[sym] = []
        self.reqAllOpenOrders()

    def get_trades(self):
        reqId = self.getId()
        self.reqExecutions(reqId, ExecutionFilter())

        self.req_buffer[reqId] = []

    def trade(self, symbol, side, t, qty, lmt_price=None):
        order = Order()
        order.action = side
        order.totalQuantity = qty
        order.orderType = t
        if lmt_price != None:
            order.lmtPrice = self.round_price(lmt_price, symbol)

        self.placeOrder(self.nextOrderId, self.contract(symbol), order)
        self.nextOrderId += 1

    def cancel(self, orderId):
        self.cancelOrder(orderId)

    def cancel_all(self, symbol, side='all'):
        if symbol in self.orders.keys():
            if side == 'all':
                return [self.cancel(ord['orderId']) for ord in self.orders[symbol]]
            return [self.cancel(ord['orderId']) for ord in self.orders[symbol] if ord['side'] == side]

    def position(self, account: str, contract: Contract, position: float, avgCost: float):
        self.balance[contract.symbol] = position

    def execDetails(self, reqId: int, contract: Contract, execution: Execution):
        try:
            entry = {'symbol': contract.symbol, 'orderId': execution.orderId,
                    'qty': execution.shares, 'price': execution.price, 'side': 'BUY' if execution.side == 'BOT' else 'SELL'}

            self.req_buffer[reqId].append(entry)
        except Exception as e:
            print(f'err, invalid execDetail reqId: {reqId}')

    def execDetailsEnd(self, reqId: int):
        trades = dict([(k,[]) for k, v in self.trades.items()])
        if reqId in self.req_buffer.keys():
            for trd in self.req_buffer[reqId]:
                if trd['symbol'] not in trades.keys():
                    trades[trd['symbol']] = []
                trades[trd['symbol']].append(trd)
                
            del self.req_buffer[reqId]
            self.trades = trades

    def nextValidId(self, orderId: int):
        super().nextValidId(orderId)
        self.nextOrderId = orderId

    def openOrder(self, orderId, contract, order, orderState):
        entry = {'symbol': contract.symbol, 'orderId': order.orderId, 'type':order.orderType, 'qty': order.totalQuantity, 'price': order.lmtPrice, 'side': order.action}
        if contract.symbol in self.orders.keys():
            for i, ord in enumerate(self.orders[contract.symbol]):
                if ord['orderId'] == orderId:
                    self.orders[contract.symbol][i] = ord
                    return
            self.orders[contract.symbol].append(entry)

    def openOrderEnd(self):
        super().openOrderEnd()

    def tickPrice(self, reqId, tickType, price, attrib):
        tick_str = TickTypeEnum.idx2name[tickType]
        symbol = self.req_buffer[reqId]
        """
        if tick_str in ['DELAYED_BID', 'BID']:
            self.bids[symbol] = [price]
        if tick_str in ['DELAYED_ASK', 'ASK']:
            self.asks[symbol] = [price]
        if tick_str in ['DELAYED_LAST', 'CLOSE']:
            self.price[symbol] = [price]"""

    def historicalData(self, reqId, bar):
        entry = {'time': bar.date, 'open': bar.open, 'high': bar.high,
                 'low': bar.low, 'close': bar.close, 'volume': bar.volume}
        self.entry_buffer[reqId].append(entry)

    def historicalDataEnd(self, reqId: int, start: str, end: str):
        self.past_klines[self.req_buffer[reqId]] = {}
        self.past_klines[self.req_buffer[reqId]][self.interval_buffer[reqId]] = self.entry_buffer[reqId]

    def accountSummary(self, reqId: int, account: str, tag: str, value: str, currency: str):
        try:
            self.acc_info[tag] = float(value)
        except:
            self.acc_info[tag] = value

        if tag == "CashBalance":
            self.balance[self.currency] = float(value)

        return super().accountSummary(reqId, account, tag, value, currency)

    def accountSummaryEnd(self, reqId: int):
        return super().accountSummaryEnd(reqId)

    def contract (self,symbol):
        contract = Contract()
        contract.symbol = symbol
        contract.secType = 'STK'
        contract.exchange = 'SMART'
        contract.currency = 'USD'
        return contract

    def getId(self):
        self.__last_id += 1
        return self.__last_id

    def contractDetails(self, reqId: int, contractDetails: ContractDetails):
        #return super().contractDetails(reqId, contractDetails)
        symbol = contractDetails.contract.symbol
        if symbol not in self.exchange_info.keys():
            self.exchange_info[symbol] = {}
        self.exchange_info[symbol]['stepSize'] = contractDetails.minTick

    def update_exchange_info(self):
        for contract in self.contracts.values():
            if contract.symbol not in self.exchange_info.keys():
                self.exchange_info[contract.symbol] = {}
            self.reqContractDetails(self.getId(), contract)

    def round_price(self, price, symbol):
        size = 1 / float(self.exchange_info[symbol]['stepSize'])
        result = round(math.floor(price * size) / size, 9)
        return result
