class ReservedAccount:
    def __init__ (self, label, fm):
        self.label = label
        self.fm = fm
        self.filename = f"{self.label}_reserved_acc"
        self.content={}
        try:
            self.content = self.fm.load(self.filename)
        except FileNotFoundError:
            self.__create()

    def cut (self, time, balance):
        self.content['time'] = time
        self.content['balance'] = balance
        self.fm.save(self.content, self.filename)

    def add_order(self, orderId):
        self.content['orders'].append(orderId)
        self.fm.save(self.content, self.filename)

   def __create(self):
        self.content = {"time":-1,
                       "orders" [],
                       "balance" [],}
        self.fm.save(content, self.filename)
