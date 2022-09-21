import time
from datetime import datetime, timedelta, date
import pandas as pd
import numpy as np
import requests
import json
import math
from binance.spot import Spot


def tickermap(ticker):
  ticker = ticker.strip().replace('-', " ")
  ticker = ticker.strip().replace('/', " ")
  ticker = ticker.upper()
  url = "https://quotes-gw.webullfintech.com/api/search/pc/tickers?keyword={}&pageIndex=1&pageSize=20".format(
      ticker)
  #headers = {'access_token': 'dc_us1.1771c1462b7-ac3d4a4af93a491e936545d00ef9aa02'}
  req = requests.get(url=url).json()
  try:
    for re in req['data']:
      if re['symbol'] == ticker:
        return re['tickerId']
        break
  except:
    print("No symbol is matched!")


def clmultimin(tickeridn, tmin, tidn):
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

  url = 'https://quotes-gw.webullfintech.com/api/quote/charts/query?tickerIds={}&type={}&count=1200&timestamp={}'.format(tickeridn, tmin, tidn)
  resp = requests.get(url, headers=headers).json()
  return resp[0]['data']

  stdout, stderr = process.communicate()
  a = json.loads(stdout.decode('utf-8'))
  return a[0]['data']


def webull(symbols, mins, days):

  dfs = []
  for ticker in symbols:
    rng = math.ceil(390 * days / mins / 1199)
    dff = pd.DataFrame()
    tickerid = tickermap(ticker)
    if ticker == "BTCUSD":
      tickerid = 950160802
    mvar = 'm{}'.format(mins)
    tvar = '{}T'.format(mins)
    for i in range(rng):
        try:
          if i == 0:
            d = datetime.now()
            txs = clmultimin(tickerid, mvar, int(datetime.timestamp(d)))
          else:
            txs = clmultimin(tickerid, mvar, nd)
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

    dff = dff.reset_index(drop=True)[
        ['timestamp', 'open', 'high', 'low', 'close', 'volume', "ticker"]]
    #dff['timestamp'] = pd.to_datetime(dff['timestamp'])
    dff = dff.rename(columns={'timestamp': "time",
                     'ticker': "symbol"})

    target = datetime.now() - timedelta(days=days)
    dff = dff.loc[dff['time'] >= target.timestamp()]
    dfs.append(dff)
  merged = pd.concat(dfs).sort_values(['time', 'symbol']).reset_index()
  merged['time'] *= 1000
  return merged



def binance(symbols, lookback, interval):
  weight_high = 0
  start_time = time.time()
  client = Spot(show_limit_usage=True)
  kline_dict = {}
  for sym in symbols:
    start = int((datetime.now() - lookback).timestamp() * 1000)
    klines = []
    while 1:
      resp = client.klines(sym, interval, startTime=start, limit=1000)
      try:
        weight = int(resp['limit_usage']['x-mbx-used-weight-1m'])
        weight_high = max(weight, weight_high)
        if weight > 1100:
          return 'Too much data to scrape.'
      except:
        return 'Limit couldnt be received'
      df = pd.DataFrame(resp['data'])
      df = df.rename(columns={0: 'time', 1: 'open', 2: 'high', 3: 'low', 4: 'close', 5: 'volume'})
      df = df.astype({'open': 'float64', 'close': 'float64', 'high': 'float64', 'low': 'float64'})
      start = df.iloc[-1]['time']
      klines.append(df)
      if len(df) != 1000:
        break
    full_kline = pd.concat(klines)
    full_kline = full_kline[['time', 'open', 'high', 'low', 'close', 'volume']].reset_index(drop=True)
    full_kline['symbol'] = sym
    kline_dict[sym] = full_kline
  output = (pd.concat(kline_dict.values())).sort_values(['time', 'symbol'])
  print(
      f'Took {round(time.time() - start_time,2)} seconds. (weight={weight_high})')
  return output


class Webull:
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

  def get_price(symbol):
    url = f'https://quotes-gw.webullfintech.com/api/stock/tickerRealTime/getQuote?tickerId={tickermap(symbol)}&includeSecu=1&includeQuote=1&more=1'
    resp = requests.get(url)
    return float(resp.json()['close'])


  def tickermap(ticker):
    ticker = ticker.strip().replace('-', " ")
    ticker = ticker.strip().replace('/', " ")
    ticker = ticker.upper()
    url = "https://quotes-gw.webullfintech.com/api/search/pc/tickers?keyword={}&pageIndex=1&pageSize=20".format(
        ticker)
    #headers = {'access_token': 'dc_us1.1771c1462b7-ac3d4a4af93a491e936545d00ef9aa02'}
    req = requests.get(url=url).json()
    try:
      for re in req['data']:
        if re['symbol'] == ticker:
          return re['tickerId']
          break
    except:
      print("No symbol is matched!")


  def get_klines_day(ticker):
    url = f"https://quotes-gw.webullfintech.com/api/quote/charts/query?period=m1&tickerIds={tickermap(ticker)}"
    data = requests.get(url).json()[0]['data']
    rows = [{"time": row.split(',')[0],
             "open": row.split(',')[1],
             "high": row.split(',')[3],
             "low": row.split(',')[4],
             "close": row.split(',')[2],
             "volume": row.split(',')[6]} for row in data]
    df = pd.DataFrame(rows)
    return df


  def get_klines_min(symbols, mins, days):
    dfs = []
    for ticker in symbols:
      rng = math.ceil(390 * days / mins / 1199)
      dff = pd.DataFrame()
      tickerid = tickermap(ticker)
      if ticker == "BTCUSD":
        tickerid = 950160802
      mvar = 'm{}'.format(mins)
      tvar = '{}T'.format(mins)

      def clmultimin(tickeridn, tmin, tidn): return requests.get(
          'https://quotes-gw.webullfintech.com/api/quote/charts/query?tickerIds={}&type={}&count=1200&timestamp={}'.format(tickeridn, tmin, tidn), headers=Webull.headers).json()[0]['data']

      for i in range(rng):
          try:
            if i == 0:
              d = datetime.now()
              txs = clmultimin(tickerid, mvar, int(datetime.timestamp(d)))
            else:
              txs = clmultimin(tickerid, mvar, nd)
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
      dff = dff.reset_index(drop=True)[
          ['timestamp', 'open', 'high', 'low', 'close', 'volume', "ticker"]]
      #dff['timestamp'] = pd.to_datetime(dff['timestamp'])
      dff = dff.rename(columns={'timestamp': "time",
                      'ticker': "symbol"})

      target = datetime.now() - timedelta(days=days)
      dff = dff.loc[dff['time'] >= target.timestamp()]
      dfs.append(dff)
    merged = pd.concat(dfs).sort_values(['time', 'symbol']).reset_index()
    merged['time'] *= 1000
    return merged
