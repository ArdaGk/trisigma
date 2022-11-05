from trisigma.stream import Stream
from alg import Alg
import os
import sys
DATA_PATH = os.path.join(os.getcwd(), "appdata/")
LABEL = sys.argv[1]
API_KEY = os.getenv("BINANCE_API")
SECRET_KEY = os.getenv("BINANCE_SECRET")

SYMBOLS =  [{'symbol': 'LINKUSDT', 'freq': '20s', 'balance': 45},
            {'symbol': 'ETHUSDT', 'freq': '20s', 'balance': 45},
            {'symbol': 'LTCUSDT', 'freq': '20s', 'balance': 45},
            {'symbol': 'SOLUSDT', 'freq': '20s', 'balance': 45},
            {'symbol': 'AVAXUSDT', 'freq': '20s', 'balance': 45},
            {'symbol': 'ALGOUSDT', 'freq': '20s', 'balance': 45},
            {'symbol': 'UNIUSDT', 'freq': '20s', 'balance': 45},
            {'symbol': 'AAVEUSDT', 'freq': '20s', 'balance': 45},
            {'symbol': 'MATICUSDT', 'freq': '20s', 'balance': 45},]

conf = {'alg':Alg,
    'load': {'15m': 96*2, '1w': 5},
    'freq': '5s',
    'platform': 'binance',
    'symbols': SYMBOLS,
    'api_key': API_KEY,
    'secret_key': SECRET_KEY,
    'label':LABEL,
    'fm': DATA_PATH}


Stream(conf).connect()


