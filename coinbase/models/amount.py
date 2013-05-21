__author__ = 'gsibble'

class CoinbaseAmount(float):

    def __new__(self, amount, currency):
        return float.__new__(self, amount)

    def __init__(self, amount, currency):
        super(CoinbaseAmount, self).__init__()
        self.currency = currency
