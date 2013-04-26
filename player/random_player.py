from random import getrandbits, choice
from simpleplayer import SimplePlayer


class RandomPlayer(SimplePlayer):
    """
    This player implements the following strategy:
        a random strategy, which randomly chooses a tile from the
        player's pool and buys a random number of shares (aka stock
        certificates) for random hotels.

    """

    # @Postcondition(lambda: isinstance(__return__, TileMove), globals=globals())
    def _place_tile(self, state):
        """
        Contract inhereted from Player

        This player randomly selects one of his tiles to play.

        """
        return choice(self.valid_tile_moves(state))

    # @Postcondition(lambda: isinstance(__return__, BuyMove), globals=globals())
    def _buy_stock(self, state):
        """
        Contract inherited from Player

        This player will select a random number of shares to buy (up to the max), and for each of
            those 'purchases' chooses a random in-play hotel he can afford.
        This player will select shares by that algorithm until there are no hotels that he can purchase,
            it may be that there are no such hotels.

        """
        return choice(self.valid_buy_orders(state))

    def keep(self, state, hotels):
        return [bool(getrandbits(1)) for _ in hotels]


import unittest as ut
from board import Board
from basics import *
from state import GameStatePlayer, GameState
class TestRandomPlayer(ut.TestCase):


    def test_tile_placement(self):

        board_singleton = Board._board_in_play(dict([]))
        players_singleton = [GameStatePlayer._test_gsplayer("foo", 6000, dict([]), set(['2B']))]
        player = RandomPlayer('foo')

        tile, hotel, movetype = player._place_tile(GameState._game_state_in_progress(players_singleton, board_singleton))

        self.assertEquals(tile, '2B')
        self.assertEquals(hotel, None)
        self.assertEquals(movetype, SINGLETON)


        test_board = [(C, ['3E', '4E']), (I, ['5G', '3G', '4G'])]
        board_merge = Board._board_in_play(test_board)
        players_merge = [GameStatePlayer._test_gsplayer("foo", 6000, dict([]), set(['3F']))]

        tile, hotel, movetype = player._place_tile(GameState._game_state_in_progress(players_merge, board_merge))

        self.assertEquals(tile, '3F')
        self.assertTrue(hotel in ['Continental', 'Imperial'])
        self.assertEquals(movetype, MERGE)



    def test_buy_stock(self):

        board = Board._board_in_play([(S, ['5G', '6G'])])
        players = [GameStatePlayer._test_gsplayer("foo", 6000, dict([('Sackson', 3)]), set(['2B']))]

        player = RandomPlayer('foo')
        buys = player._buy_stock(GameState._game_state_in_progress(players, board))

        self.assertTrue(len(buys)<=2)
        if len(buys)!=0:
            self.assertTrue(buys[0]!='Worldwide')

    def test_keeps(self):

        board = Board._board_in_play([(S, ['5G', '6G']), (F, ['1A', '2A'])])
        players = [GameStatePlayer._test_gsplayer("foo", 200, dict([('American', 3), ('Festival', 5)]), set())]

        player = RandomPlayer('foo')
        keeps = player.keep(GameState._game_state_in_progress(players, board), [A])
        self.assertEquals(len(keeps), 1)

        keeps = player.keep(GameState._game_state_in_progress(players, board), [A, F])
        self.assertEquals(len(keeps), 2)


if __name__ == '__main__':
    ut.main()
