from ordered_player import OrderedPlayer
from basics import *
from random import randrange, choice

class KeepCheater(OrderedPlayer):

    def keep(self, state, hotels):
        if randrange(10) == 0:
            #cheat
            return [True, False, True, False]
        else:
            return OrderedPlayer.keep(self, state)


