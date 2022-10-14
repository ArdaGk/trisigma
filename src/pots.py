class PotManager:

    grand_balance = 500

    def __init__(self, broker, perc) -> None:
        self.broker = broker
        self.perc = perc
        self.reserved_balance = 0

class ReservedPots:
    def __init__ (self, broker, amount):
        self.broker = broker
        self.start = broker.get_timestamp()
        self.amount = amount
    def get_balance(self):
        trades = list(filter(lambda trd: trd['time'] > self.start, self.broker.trades))
        profit = sum([-trd["quoteQty"] if trd['side'] == 'BUY' else trd['quoteQty'] for trd in trades])
        return self.amount + profit