from binance.spot import Spot
from datetime import datetime, timedelta
import math
import copy
#Concerns
#needs better trade error detection than looking for orderId
#orderId as dict not list (identical ids in multisymbol)
#Predetermined quote asset
#No caution for partially filleds
#Init capital hardcoded
#skipping in balances for the speed
#show_limit_usage=True assumed
#self.ignore = ["BNB"] for slicing in the future
#needs label passed
class ReservedSpot (Spot):
    def __init__ (self, *args, label="generic", fm=None, start_balance=300, **kwargs):
        super().__init__(*args, **kwargs)
        self.label = label
        self.fm = fm
        self.init_capital=start_balance
        self.filename = f"{self.label}_reserved_acc"
        self.balances = {}
        self.quote_asset = 'USDT'
        self.__load()

        self.filt = lambda arr: [x for x in arr if x['orderId'] in self.orderIds]
    def cancel_order (self, *args, **kwargs):
        resp = super().cancel_order(*args, **kwargs)
        return resp

    def cancel_open_orders (self, *args, **kwargs):
        orders = self.get_open_orders(args[0])
        all_resps = [self.cancel_order(args[0], o['orderId']) for o in orders['data']]
        weight = orders['limit_usage']['x-mbx-used-weight']
        data = []
        for r in all_resps:
            weight += float(r['limit_usage']['x-mbx-used-weight'])
            data.append(r['data'])
        resp = {'data': data, 'limit_usage':{'x-mbx-used-weight': str(weight), 'x-mbx-used-weight-1m': str(weight)}}
        return resp

    def new_order (self, *args, **kwargs):
        resp = super().new_order(*args, **kwargs)
        if 'orderId' in resp['data'].keys():
            self.orderIds.append(resp['data']['orderId'])
            self.__save()
        self.all_orders[args[0]] = super().get_orders(args[0])['data']
        return resp

    def get_open_orders (self, *args, **kwargs):
        resp = super().get_open_orders(*args, **kwargs)
        filtered = self.filt(resp['data'])
        resp['data'] = filtered
        return resp


    def my_trades (self, *args, **kwargs):
        resp = super().my_trades(*args, **kwargs)
        filtered = self.filt(resp['data'])
        resp['data'] = filtered
        return resp

    def account (self, *args, **kwargs):
        resp = super().account(*args, **kwargs)
        #Update all_orders
        executions = self.__get_executions(resp['data']['balances'])
        quote_asset = self.quote_asset
        for asset in executions:
            if asset == quote_asset:
                continue
            symbol = asset + quote_asset
            print(f"{symbol} get_orders (change detected)")
            self.all_orders[symbol] = super().get_orders(symbol)['data']


        balance=[]
        quote = 0
        quote_locked=0
        for bal in resp['data']['balances']:
            #quote asset is skipped
            if bal['asset'] == quote_asset:
                continue
            symbol = bal['asset'] + quote_asset
            if symbol not in self.all_orders.keys():
                if float(bal['free']) + float(bal['locked']) == 0:
                    entry = {"asset": bal['asset'], "free":0, "locked":0}
                    balance.append(entry)
                    continue
                else:
                    print(f"{symbol} get_orders (init)")
                    self.all_orders[symbol] = super().get_orders(symbol)['data']
            orders = self.all_orders[symbol]
            #cut balance is zero
            #orders are up to date
            full=0
            locked=0
            for order in orders:
                if order['orderId'] not in self.orderIds:
                    continue
                sign = -1 if order['side'] == 'SELL' else 1
                if order['status'] == "FILLED":
                    full+=float(order['executedQty'])*sign
                    quote+=float(order['cummulativeQuoteQty'])*-sign
                if order['status'] == "NEW":
                    if sign == -1: #LIMIT SELL
                        locked+=(float(order['origQty']) - float(order['executedQty']))
                    if sign == 1: #LIMIT BUY
                        qty = float(order['origQty']) - float(order['executedQty'])
                        price = float(order['price'])
                        quote_locked+=qty*price
            entry = {"asset": bal['asset'], "free":full-locked, "locked":locked}
            balance.append(entry)
            self.balances[bal['asset']] = entry
        quote_bal = {"asset": quote_asset, "free":self.init_capital + quote-quote_locked, "locked":quote_locked}
        balance.append(quote_bal)
        self.balances[quote_asset] = quote_bal
        resp['data']['balances'] = balance
        return resp

    def __get_executions (self, account):
        new_balance = {asset['asset']: asset for asset in account}
        #Initialize
        if self.old_balance == {}:
            self.old_balance = new_balance
            return []
        output = []
        for k, v in new_balance.items():
            if k in self.old_balance.keys():
                if self.old_balance[k] == v:
                    continue
            print(f"new execution: {k}")
            output.append(k)
        self.old_balance = new_balance
        return output

    def __save(self):
        data = {"orderIds": self.orderIds, "all_orders":self.all_orders, "old_balance":self.old_balance}
        self.fm.save(data, self.filename)
    def __load(self):
        try:
            data = self.fm.load(self.filename)
            self.orderIds = data['orderIds']
            self.all_orders = data['all_orders']
            self.old_balance = data['old_balance']
        except FileNotFoundError:
            self.orderIds = []
            self.all_orders = {}
            self.old_balance = {}
            

