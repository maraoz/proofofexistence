__author__ = 'gsibble'

class CoinbaseUser(object):

    def __init__(self,
                 user_id,
                 name,
                 email,
                 time_zone,
                 native_currency,
                 balance,
                 buy_level,
                 sell_level,
                 buy_limit,
                 sell_limit):

        self.id = user_id
        self.name = name
        self.email = email
        self.time_zone = time_zone
        self.native_currency = native_currency
        self.balance = balance
        self.buy_level = buy_level
        self.sell_level = sell_level
        self.buy_limit = buy_limit
        self.sell_limit = sell_limit