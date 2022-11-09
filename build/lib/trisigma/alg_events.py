class BaseListener:
    def __init__(self):
        self.events = []

    def add(self, func, cond, args=[]):
        self.events.append((func, cond, args))

    def remove(self, func):
        #if func in self.events.keys():
        #del self.events[func]
        pass
