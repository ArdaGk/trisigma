from datetime import datetime, timedelta
from trisigma.time_utils import to_timestamp, to_timestamp_split, BadIntervalError
from webull import paper_webull
import json
import requests
import pandas as pd
import time
import numpy as np
from datetime import datetime, date
#Access token expire error
#Access via webull and rewrite over time
#Bid/Ask missing
#Get_klines must be tested with single lookback during trading hours
#Stuff might be different on real account
#Order count 200 must be foreach
#avg filled price (2 use case)
#No isBuyer, isMakerr
#time as datetime
#ping target can get deprecated
#price individual, pulled at broker-time
#get_price lookback
#cancel single thread
#other brokers might not have cancelall "side" option
#Cant get above 4h
#get_ohlc, pull_ohlc, get_klines requires heavy refactoring

class Client:
    def __init__ (self, cred, load, symbols, label, fm):
        self.wb = self.login(cred)
        self.symbols = symbols
        self.label = label
        self.fm = fm
        self.quotes = {}
        self.trades = {}
        self.account = {}
        self.klines = {}
        self.load = load

    def login (self, cred):
        wb = paper_webull()
        with open(cred, "r") as f:
            result = json.load(f)
            wb._refresh_token = result['refreshToken']
            wb._access_token = result['accessToken']
            wb._token_expire = result['tokenExpireTime']
            wb._uuid = result['uuid']
            n_result = wb.refresh_login()
            result['refreshToken'] = n_result['refreshToken']
            result['accessToken'] = n_result['accessToken']
            result['tokenExpireTime'] = n_result['tokenExpireTime']
        with open(cred, "w") as f:
            json.dump(result, f)
        return wb

    def update (self, symbol):
        self.account = self.wb.get_account()
        self.trades = self.get_trades()
        #self.latency = self.ping()
        self.quotes[symbol] = self.get_quote(symbol)
        self.klines[symbol] = self.get_market_data(symbol)

    def get_quote (self, symbol):
        resp = self.wb.get_quote(symbol)
        bid = float(resp['bidList'][0]['price'])
        ask = float(resp['askList'][0]['price'])
        price = float(resp['close'])
        return {"price": price, "bid": bid, "ask": ask}

    def get_market_data (self, symbol):
        data = {}
        for k, v in self.load.items():
            data[k] = self.pull_klines(symbol, k, v)
        return data

    def get_trades (self):
        orders = self.wb.get_history_orders(status="Filled",count=200)
        trades = {}
        for order in orders:
            sym = order['ticker']['symbol']
            if sym not in trades.keys():
                trades[sym] = []
            trades[order['ticker']['symbol']].append(order)
        return trades

    def trade(self, symbol, typ, side, qty, limit_price = None, enforce = "GTC"):
        if typ.upper() in ['MARKET', 'MKT']:
            order = self.wb.place_order(stock=symbol, action=side, orderType="MKT", quant=qty, enforce="DAY")
        elif typ.upper() in ['LIMIT', 'LMT']:
            order = self.wb.place_order(stock=symbol, action=side, orderType="LMT", price=limit_price, enforce=enforce, quant=qty)
        else:
            raise Exception(f"err, Unknown order type: {typ}")
        return order

    def get_timestamp (self):
        return datetime.now().timestamp()

    def ping (self, target="https://quotes-gw.webullfintech.com"):
        start = datetime.now().timestamp()
        requests.get(target)
        latency = (datetime.now().timestamp()-start) * 1000
        return latency


    def __tickermap(self, ticker):
        ticker = ticker.strip().replace('-', " ")
        ticker = ticker.strip().replace('/', " ")
        ticker = ticker.upper()
        url = "https://quotes-gw.webullfintech.com/api/search/pc/tickers?keyword={}&pageIndex=1&pageSize=20".format( ticker)
        req = requests.get(url=url).json()
        try:
            for re in req['data']:
                if re['symbol'] == ticker:
                    return re['tickerId']
                break
        except:
            print("No symbol is matched!")

    def pull_klines(self, ticker, interval, lookback):
        step, mins = self.get_step(interval)
        step_lookback= lookback*int(step)

        headers = { 'sec-ch-ua': '"Chromium";v="94", "Google Chrome";v="94", ";Not A Brand";v="99"',
                'device-type': 'Web',
                'did': '25970a42e9a34894955769aaea8f5600',
                'ph': 'MacOS Chrome',
                'os': 'web',
                'tz': 'America/Chicago',
                'sec-ch-ua-platform': '"macOS"',
                'reqid': '6c3f0dfbe2bf452e824d9b00d0e8452a',
                'hl': 'en',
                'locale': 'eng',
                'sec-ch-ua-mobile': '?0',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36',
                'Referer': 'https',
                'app': 'global',
                'platform': 'web',
                'ver': '3.37.7',
                'osv': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36'}
        
        rng = (step_lookback // 1200) + 1
        dff = pd.DataFrame()
        tickerid = self.__tickermap(ticker)
        if ticker == "BTCUSD":
            tickerid = 950160802
        minvar = 'm{}'.format(int(mins))
        tvar = '{}T'.format(mins) #Added later
        def clmultimin(tickeridn, tmin, tidn): return requests.get(
            'https://quotes-gw.webullfintech.com/api/quote/charts/query?tickerIds={}&type={}&count=1200&timestamp={}'.format(tickeridn, tmin, tidn), headers=headers).json()[0]['data']
        for i in range(int(rng)):
            try:
                if i == 0:
                    d = datetime.now()
                    txs = clmultimin(tickerid, minvar, int(datetime.timestamp(d)))
                else:
                    txs = clmultimin(tickerid, minvar, nd)
                l = []
                for tx in txs[:-1]:
                    try:
                        l.append([ticker, int(tx.split(",")[0]), float(tx.split(",")[1]), float(tx.split(",")[2]), float(
                            tx.split(",")[3]), float(tx.split(",")[4]), float(tx.split(",")[6]), float(tx.split(",")[7])])
                    except:
                        l.append([ticker, int(tx.split(",")[0]), float(tx.split(",")[1]), float(tx.split(",")[
                        2]), float(tx.split(",")[3]), float(tx.split(",")[4]), float(tx.split(",")[6]), 0])
                df = pd.DataFrame(l)
                df.columns = ['ticker', 'date', 'open',
                            'close', 'high', 'low', 'volume', 'vwap']
                df.date = df.date.apply(lambda d: time.strftime(
                    '%Y-%m-%d %H:%M:%S', time.gmtime(d)))
                df['timestamp'] = df.date.apply(
                    lambda d: datetime.strptime(d, '%Y-%m-%d %H:%M:%S').timestamp())
                df['date1'] = df.date.apply(
                    lambda d: datetime.strptime(d, '%Y-%m-%d %H:%M:%S').date())
                df['date2'] = df.date.apply(
                    lambda d: datetime.strptime(d, '%Y-%m-%d %H:%M:%S'))
                df['date3'] = df['date2'].dt.tz_localize(
                    'GMT').dt.tz_convert('US/Central').dt.tz_localize(None)
                df.set_index('date3', inplace=True)
                dff = pd.concat([dff, df], axis=0)
                dff.sort_index(ascending=True, inplace=True)

                nd = int(txs[-1].split(",")[0])
            except Exception as e:
                print(e)

        url = f"https://quotes-gw.webullfintech.com/api/quote/charts/query?tickerIds={tickerid}&type=d1&count=800"
        headers = {
        'access_token': 'dc_us1.1771c1462b7-ac3d4a4af93a491e936545d00ef9aa02'}
        req = requests.get(url=url, headers=headers).json()
        try:
            dff['dayv'] = dff.index.date
            dvar = int(req[0]['split'][0]['date'][:4])
            mvar = int(req[0]['split'][0]['date'][5:7])
            dyvar = int(req[0]['split'][0]['date'][9:])
            svar = int(int(req[0]['split'][0]['splitTo']) /
                    int(req[0]['split'][0]['splitFrom']))
            dff['open'] = np.where(dff['dayv'] < date(
                dvar, mvar, dyvar), dff['open']/svar, dff['open'])
            dff['close'] = np.where(dff['dayv'] < date(
                dvar, mvar, dyvar), dff['close']/svar, dff['close'])
            dff['high'] = np.where(dff['dayv'] < date(
                dvar, mvar, dyvar), dff['high']/svar, dff['high'])
            dff['low'] = np.where(dff['dayv'] < date(
                dvar, mvar, dyvar), dff['low']/svar, dff['low'])
            dff.drop('dayv', axis=1, inplace=True)
        except:
            pass
        dff = dff.reset_index(drop=True)[['timestamp', 'open', 'high', 'low', 'close', 'volume', "ticker"]]
        dff = dff.rename(columns={'timestamp': "time_index",'ticker': "symbol"})
        dff['time_index']-=mins*60
        dff['time'] = dff['time_index']
        dff['time_index'] = pd.to_datetime(dff['time_index'], unit='s')

        translator = {1: 'S', 60: 'MIN', 3600: 'H', 86400: 'D', 604800: 'W', 31536000:'Y'}
        coef, sec = to_timestamp_split(interval)
        translated_interval = f"{int(coef)}{translator[int(sec)]}"
        dff = dff.set_index("time_index").resample(translated_interval).agg({'time': "first", 'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'}).reset_index(drop=True).dropna()
        return dff[-lookback:].reset_index(drop=True)

    def get_step (self, interval, duration=360):
        duration = 390
        factors = [1, 5, 15, 30, 60, 120, 240]
        mins = to_timestamp(interval) / 60
        if mins<5:
          return (mins, 1)
        if mins >= 86400/60:
            market_days = mins/(86400/60)
            if market_days % 1 != 0:
                raise BadIntervalError(f"interval: {interval} cannot be divided into days")
            mins = market_days * duration
            factors = [fac for fac in factors if duration % fac == 0]

        coefs = [mins / fac for fac in factors]

        for i, coef in enumerate(reversed(coefs)):
            if coef % 1 == 0:
                return (coef, factors[-(i+1)])


class Broker:
    def __init__(self, symbol, client):
        self.client = client
        self.symbol = symbol
        self.__trades = []
        self.__open_orders = {}
        self.__position = {}
        self.__balance = {}
        self.__price = -1
        self.__timestamp = 0

    def __call__(self):
        self.client.update(self.symbol)
        trades = []
        open_orders = {"BUY":[], "SELL":[]}
        position = {"full": 0, "free": 0, "locked": 0}
        balance = {}
        translator = {"Working": "NEW", "LMT": "LIMIT", "MKT": "MARKET"}
        locked_cash = 0

        #Get open_orders
        for order in self.client.account['openOrders']:
            if order['status'] == "PendingCancel":
                continue
            sym = order['ticker']['symbol']
            if order['action'] == "BUY":
                locked_cash += (float(order["totalQuantity"]) - float(order['filledQuantity'])) * float(order["lmtPrice"])
            if sym == self.symbol:
                entry = {"orderId": int(order['orderId']),
                        "time": int(order["createTime0"]),
                        "symbol": sym,
                        "side": order['action'],
                        "price": float(order["lmtPrice"]),
                        "origQty": float(order["totalQuantity"]),
                        "filledQty": float(order["filledQuantity"]),
                        "status": translator[order["status"]],
                        "timeInForce": order["timeInForce"],
                        "type": translator[order['orderType']]}

                open_orders[order['action']].append(entry)

        #Get previous trades
        if self.symbol not in self.client.trades.keys():
            self.client.trades[self.symbol] = []
        for trd in self.client.trades[self.symbol]:
            entry = {"orderId": int(trd['orderId']),
                    "time": int(trd["filledTime0"]),
                    "symbol": self.symbol,
                    "side": trd['action'],
                    "price": float(trd["avgFilledPrice"]),
                    "qty": float(trd["totalQuantity"]),
                    "quoteQty": float(trd["totalQuantity"])*float(trd["avgFilledPrice"]),
                    "type": translator[trd['orderType']],
                    "commission": 0,
                    "commissionAsset": "USD"}
            trades.append(entry)

        # Get position
        for pos in self.client.account['positions']:
            if pos['ticker']['symbol'] == self.symbol:
                full = float(pos['position'])
                locked = sum([order['origQty'] - order["filledQty"] for order in open_orders['SELL']])
                free = full - locked
                position = {"full": full, "free": free, "locked": locked}

        #Get account balance (USD)
        for mem in self.client.account['accountMembers']:
            if mem['key'] == 'usableCash':
                free = float(mem['value'])
                full = free + locked_cash
                balance = {"full": full, "free": free, "locked": locked_cash}

        self.__timestamp = self.client.get_timestamp()
        self.__price = self.client.quotes[self.symbol]['price']
        self.__position = position
        self.__balance = balance
        self.__open_orders = open_orders
        self.__trades = trades

    def buy(self, _type, qty, limit_price=None):
        order = self.client.trade(self.symbol, _type, "BUY", qty, limit_price)
        return order

    def quote_buy(self, _type, quote_price, limit_price=None):
        qty = quote_price / self.get_price()
        order = self.client.trade(self.symbol, _type, "BUY", qty, limit_price)
        return order

    def sell(self, _type, qty, limit_price=None):
        order = self.client.trade(self.symbol, _type, "SELL", qty, limit_price)
        return order

    def quote_sell(self, _type, quote_price, limit_price=None):
        qty = quote_price / self.get_price()
        order = self.client.trade(self.symbol, _type, "SELL", qty, limit_price)
        return order

    def cancel(self, orderId):
        return self.client.cancel(self.symbol, orderId)


    def cancel_all(self, side='ALL'):
        side = side.upper()
        orders = self.__open_orders['BUY'] + self.__open_orders['SELL'] if side == 'ALL' else self.__open_orders[side]
        ids = [order['orderId'] for order in orders]
        resp = [self.cancel(_id) for _id in ids]
        return resp

    def get_open_orders(self):
        return self.__open_orders

    def get_trades(self):
        return self.__trades

    def get_position(self):
        return self.__position

    def get_balance(self, reserved=True):
        return self.__balance

    def get_ohlc(self, interval, lookback=1):
        return self.client.klines[self.symbol][interval][:lookback]

    def get_price(self, lookback=1):
        return self.__price

    def get_time(self, of_trade=False):
        return datetime.fromtimestamp(self.__timestamp)

    def get_timestamp(self, of_trade=False):
        return self.__timestamp

    def get_bids(self):
        return

    def get_asks(self):
        return

    def get_sell_price(self):
        return

    def get_buy_price(self):
        return

    def on_trade(self, side='all', _type='all'):
        return
