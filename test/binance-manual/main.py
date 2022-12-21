from trisigma.stream import Stream
from algo import Algo
import os



DATA_PATH = os.path.join(os.path.expanduser('~'), "appdata/")
API_KEY = os.getenv("BINANCE_API")
SECRET_KEY = os.getenv("BINANCE_SECRET")
SYMBOLS =  [{'symbol': 'LINKUSDT', 'freq': '20s', 'balance': 40}, 
            {'symbol': 'ETHUSDT', 'freq': '20s', 'balance': 40},
            {'symbol': 'LTCUSDT', 'freq': '20s', 'balance': 40},
            {'symbol': 'AVAXUSDT', 'freq': '20s', 'balance': 40},
            {'symbol': 'ALGOUSDT', 'freq': '20s', 'balance': 40},
            {'symbol': 'UNIUSDT', 'freq': '20s', 'balance': 40},
            {'symbol': 'AAVEUSDT', 'freq': '20s', 'balance': 40},
            {'symbol': 'MATICUSDT', 'freq': '20s', 'balance': 40},]


conf = {'alg':Algo,
    'load': {'15m': 96*2, '1w': 5},
    'freq': '5s',
    'platform': 'binance',
    'symbols': SYMBOLS,
    'api_key': API_KEY,
    'secret_key': SECRET_KEY,
    'fm': DATA_PATH}
Stream(conf).connect()

