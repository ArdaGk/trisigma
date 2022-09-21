from re import L


class AlgException (Exception):
    def __init__ (self, message):
        super().__init__(message)

class Disconnected (Exception):
    def __init__ (self, message):
        super().__init__(message)

def err(msg, _print=False, _raise=False):
    output = {"err": msg}
    if _print:
        print(output)
    if _raise:
        raise AlgException(msg)

