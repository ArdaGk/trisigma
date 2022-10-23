from multiprocessing import Pool
import numpy as np
import multiprocessing
import subprocess
import json
import sys
#market.json symbols must be dict
#Validate test returns via manual backtest
class Tuner:
    def __init__ (self, fm, tuning_conf, alg, label='default', end_func = (lambda _id, output:(_id,output)), max_child=-1, offset=0):
        self.max_child = multiprocessing.cpu_count() if max_child == -1 else max_child
        self.fm = fm
        self.tuning_conf = tuning_conf
        self.alg = alg
        self.parameters = self.tuning_conf['parameters']
        self.market = self.tuning_conf['medium']
        self.label = label
        self.end_func = end_func
        self.max_child = max_child

        self.sources = []
        self.combs = self.get_combinations(self.parameters)
        self.size = len(self.combs)
        self.offset = offset

    def launch (self):
        try:
            keys = []
            for i in range(self.size):
                self.index = i
                key = self.get_key(i)
                keys.append(key)
                if len(keys) >= self.max_child:
                    p = Pool()
                    outputs = p.map(self.fire, keys)
                    p.close()
                    p.join()
                    [self.end_func(out) for out in outputs]
                    keys = []
        except ArithmeticError as exc:
            print(f"Engine is down. exc: ({self.index}){exc}")
            return -1

    def get_key(self, i):
        i+=self.offset
        print(f"i:{i},  len(combs): {len(self.combs)}")
        key=dict.fromkeys(self.parameters.keys(), self.combs[i])
        key={k : self.combs[i][j] for j, k in enumerate(self.parameters.keys())}
        key['_id'] = i
        key['variation_id'] = mangle(i)
        return key

    def get_combinations (self,params):
        if "__data__" in params:
            self.sources = params['__data__']
            params['__data__'] = list(range(len(params['__data__'])))
        indexed = {k: list(range(len(v))) for k, v in params.items()}
        arrs=tuple([np.array(v) for v in indexed.values()])
        combs = np.array(np.meshgrid(*arrs)).T.reshape(-1,len(arrs)).tolist()
        rendered = [[params[list(params)[i]][v] for i, v in enumerate(comb)] for comb in combs]
        return rendered

    def interruption (self):
        while True:
            resp = input('Stop the tuning? [Y/n]')
            if resp.lower() in ['y', 'yes']:
                sys.exit()
            elif resp.lower() in ['n', 'no']:
                break

    def fire (self, key):
        try:
            conf = self.create_conf(key)
            proc = subprocess.Popen(['python3', self.alg, json.dumps(conf)])
            proc.wait()
            return True
        except Exception:
            key_str = json.dumps(key).replace('\n', '')
            print(f"variation {key['variation_id']} failed, key:{key_str}")
            return False
    def create_conf (self, key):
        source = {}

        if "__data__" in key.keys():
            source = {'name': self.sources[int(key['__data__'])][0]}
            symbols = [{"symbol": sym} | key for sym in self.sources[int(key['__data__'])][1]]
            del key['__data__']
        else:
            symbols = [{"symbol": sym} | key for sym in self.market['symbols']]

        _id=key['variation_id']
        conf = {"freq": self.market['freq'], 
                "lookback": self.market["range"], 
                "symbols": symbols,
                'variation_id': _id}
        conf = conf | source
        return conf

    def next_id(self):
        return _id


def baseN(num,b,numerals="0123456789abcdefghijklmnopqrstuvwxyz"):
    return ((num == 0) and numerals[0]) or (baseN(num // b, b, numerals).lstrip(numerals[0]) + numerals[num % b])

def mangle(_id):
	return baseN(((_id+1)*1679979167)%(36**6),36)
