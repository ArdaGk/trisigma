import gspread
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

class GSheets:
    def __init__(self, conf, sa):
        self.sa = gspread.service_account(filename=conf)
        self.sh = sa.open(sa)


    def set_trades(self, trades, sheet):
        df = self.__pull_trades(trades)
        arr = [df.columns.values.tolist()] + df.values.tolist()
        wks = self.sh.worksheet(sheet)
        wks.update(arr)


    def __pull_trades(self, trd, n=90):
        df = pd.DataFrame(trd)
        df["time"] = pd.to_datetime(df["time"], unit='ms')
        df.set_index('time', inplace=True)
        df.sort_index(inplace=True)
        df = df[::-1]
        df = df[df.index > datetime.now() - timedelta(days=n)]
        df = df[df.index > datetime(2022, 6, 25)].reset_index()

        df['time'] = df['time'].values.astype(np.int64) // 10 ** 9
        df = df[['orderId', 'time', 'symbol', 'price', 'qty', 'quoteQty',
                 'commission', 'commissionAsset', 'isBuyer', 'isMaker']]
        return df




    def days_filter(df, n):
        return df[df.index > datetime.datetime.now() - datetime.timedelta(days=n)]

