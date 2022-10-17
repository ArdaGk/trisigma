import requests
import pandas as pd
from datetime import timedelta
from .time_utils import to_timestamp_split

def get_quote(symbol):
  url = f"https://query2.finance.yahoo.com/v7/finance/quote?symbols={symbol}&&region=US&lang=en-US"
  headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
  resp = requests.get(url, headers=headers)
  if resp.status_code != 200:
    print(f'API Error: {resp.status_code}')
    print(resp.text)
    return None
  data = resp.json()
  output = {}
  output['bid'] = data['quoteResponse']['result'][0]['bid']
  output['ask'] = data['quoteResponse']['result'][0]['ask']
  output['price'] = data['quoteResponse']['result'][0]['regularMarketPrice']
  return output


def get_kline(symbol, start, end, interval):
  units = {1: 's', 60: 'm', 3600: 'h', 86400: 'd', 604800: 'wk', 31536000:'y'}
  coef, unit = to_timestamp_split(interval)
  interval = f"{coef}{units[unit]}"
  length = end - start
  if length > 604800 and interval == '1m':
    mid = start + 604800
    left = get_kline(symbol, start, mid, interval)
    right = get_kline(symbol, mid, end, interval)
    df = pd.concat([left, right])
  else:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?formatted=true&crumb=ySGjoc0WFRs&lang=en-US&region=US&includeAdjustedClose=true&interval={interval}&period1={round(start)}&period2={round(end)}&events=capitalGain%7Cdiv%7Csplit&useYfid=true&corsDomain=finance.yahoo.com"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
      print(f'API Error: {resp.status_code}')
      print(resp.text)
      return None
    data = resp.json()['chart']['result'][0]['indicators']['quote'][0]
    data['time'] = resp.json()['chart']['result'][0]['timestamp']
    df = pd.DataFrame(data)

  df = df.drop_duplicates(subset='time').sort_values(by='time')
  df = df[['time', 'open', 'high', 'low', 'close', 'volume']]
  return df

