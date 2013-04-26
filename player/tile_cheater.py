from ordered_player import OrderedPlayer
from basics import *
from random import randrange, choice

class TileCheater(OrderedPlayer):

    def _place_tile(self, state):
        if randrange(10) == 0:
            #cheat
            return '1A', None, SINGLETON
        else:
            return OrderedPlayer._place_tile(self, state)
