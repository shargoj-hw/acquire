from ordered_player import OrderedPlayer
from basics import *
from random import randrange, choice

class ShareCheater(OrderedPlayer):

    def _buy_stock(self, state):
        if randrange(10) == 0:
            #cheat
            return [A, A]
        else:
            return OrderedPlayer.buy_stock(self, state)

