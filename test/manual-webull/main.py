from trisigma.stream import LiveTest
from algo import WebullTester
import os
import sys

DATA_PATH = os.path.join(os.getcwd(), "appdata/")
LABEL = "UNLABELED" if len(sys.argv) == 1 else sys.argv[1]
CREDENTIALS = os.getenv("WEBULL_TOKEN")
SYMBOLS =  [{'symbol': 'AAPL'},
            {'symbol': 'AMZN'},
            {'symbol': 'META'}]




conf = {'strategy': WebullTester,
    'load': {'15m': 96*2, '1w': 5},
    'freq': '5s',
    'platform': 'webull-paper',
    'symbols': SYMBOLS,
    'credentials': CREDENTIALS,
    'label':LABEL,
    'fm': DATA_PATH}

LiveTest(conf).connect()


