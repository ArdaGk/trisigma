import json
import os
from datetime import date, datetime


class FileManager:

    def __init__ (self, base_path=None):
        """Constructor for Filemanager
        :param base_path: the dir where data should be stores.
        """
        default = os.path.join(os.getcwd(), "algdata")
        self.dir = {}
        if os.name == 'nt':
            self.sep = '\\'
            if base_path == None:
                base_path = default
        elif os.name == 'posix':
            self.sep = '/'
            if base_path == None:
                base_path = default
        else:
            print(f'OS not supported: {os.name}')
            return None
        if base_path[-1] != self.sep:
           base_path = basepath + self.sep
        self.__setup(base_path)

    def __setup (self, base_path):
        self.dir['base'] = base_path
        self.dir['log'] = self.dir['base'] + f'log{self.sep}'
        self.dir['data'] = self.dir['base'] + f'data{self.sep}'
        self.dir['config'] = self.dir['base'] + f'config{self.sep}'
        self.dir['var'] = self.dir['data'] + f'var{self.sep}'
        self.dir['plot'] = self.dir['data'] + f'plot{self.sep}'
        self.dir['tests'] = self.dir['data'] + f'tests{self.sep}'
        self.dir['markets'] = self.dir['data'] + f'markets{self.sep}'

        [self.__mkdir(_dir) for _dir in self.dir.values()]

    def __mkdir (self,_dir):
        if not os.path.exists(_dir):
            os.mkdir(_dir)

    def log(self, name, data):
        """Append a message to a log file. (stored in algdata/logs/)
        :param name: name of the log file (without extension)
        :param data: text to append
        :type data: <str>
        """
        name = self.add_ext(name, '.txt')
        with open(self.dir['log'] + name, 'a') as file:
            file.write(self.get_time() + '\t' + str(data) + '\n')

    def save(self, output, name, _dir="var"):
        """Save a variable in "algdata/data/var/" as a json file.
        :param output: variable that will be saved.
        :param name: file name (without extension)
        """
        name = self.add_ext(name, '.json')
        with open(self.dir[_dir] + name, 'w') as file:
            json.dump(output, file)

    def load(self, name, _dir="var"):
        """Load a variable in "algdata/data/var" that was previously saved.
        :param name: name of the json file (without .json extension)
        """
        name = self.add_ext(name, '.json')
        with open(self.dir[_dir] + name, 'r') as file:
            var = json.load(file)
            return var


    def add_ext(self, filename, ext):
        fullname = filename
        if filename[-len(ext):] != ext:
            fullname = fullname + ext
        return fullname

    def append(self, item, name):
        var = self.load(name)
        if isinstance(var, list):
            var.append(item)
            self.save(var, name)
            return var
        else:
            return print('err, there is no list in here.')

    def get_time(self):
        return str(datetime.now())

