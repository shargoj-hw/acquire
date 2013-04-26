from simpleplayer import SimplePlayer
from basics  import *

class OrderedPlayer(SimplePlayer):
    """
    This player implements the following strategy:
        an ordered strategy, which picks the "smallest" tile in the
        sense of tile<=? that can be placed on the board and buys as
        many shares in hotels possible in alphabetical order

    """
    # @Postcondition(lambda: isinstance(__return__, TileMove), globals=globals())
    def _place_tile(self, state):
        """
        Contract inhereted from Player

        This player selects the 'smallest' of his tiles to play.
        If this player is doing a merge, it will choose the largest of the hotels adjacent to
            the tile it is placing.
        If this player is doing a found, it will found the first available hotel in alphabetical
            order

        Return:
            Tile, Hotel, Movetype

        """
        return sorted(self.valid_tile_moves(state), key=lambda (t, h, _): str(tile_sortkey(t))+str(h))[0]


    # @Postcondition(lambda: isinstance(__return__, BuyMove), globals=globals())
    def _buy_stock(self, state):
        """
        Contract inherited from Player

        This player will purchase as many shares as possible from the available hotels in alphabetical order

        Return:
            BuyMove

        """
        stocks = self.valid_buy_orders(state)
        stocks.sort(key=lambda k: str(BUYS_PER_TURN-len(k))+k[0] if len(k)!=0 else str(BUYS_PER_TURN))
        return stocks[0]

    def keep(self, state, hotels):
        """
        Sell all shares
        """
        return [False]*len(hotels)


import unittest as ut
from board import Board
from state import GameStatePlayer, GameState
class TestOrderedPlayer(ut.TestCase):
    def setUp(self):
        pass

    def test_tile_placement(self):
        board_singleton = Board._board_in_play(dict([]))
        players_singleton = [GameStatePlayer._test_gsplayer("foo", 6000, dict([]), set(['2B', '1A', '3D']))]
        player = OrderedPlayer('foo')

        tile, hotel, movetype = player._place_tile(GameState._game_state_in_progress(players_singleton, board_singleton))

        self.assertEquals(tile, '1A')
        self.assertEquals(hotel, None)
        self.assertEquals(movetype, SINGLETON)


        test_board = [(C, ['3E', '4E']), (I, ['5G', '3G', '4G'])]
        board_merge = Board._board_in_play(test_board)
        players_merge = [GameStatePlayer._test_gsplayer("foo", 6000, dict([]), set(['3F', '6G', '3H']))]

        tile, hotel, movetype = player._place_tile(GameState._game_state_in_progress(players_merge, board_merge))

        self.assertEquals(tile, '3F')
        self.assertEquals(hotel, "Imperial")
        self.assertEquals(movetype, MERGE)


    def test_buy_stock(self):

        board = Board._board_in_play([(S, ['5G', '6G']), (F, ['1A', '2A'])])
        players = [GameStatePlayer._test_gsplayer("foo", 200, dict([('American', 3), ('Festival', 5)]), set())]

        player = OrderedPlayer('foo')
        buys = player._buy_stock(GameState._game_state_in_progress(players, board))
        self.assertEquals(buys, ['American'])


    def test_keeps(self):

        board = Board._board_in_play([(S, ['5G', '6G']), (F, ['1A', '2A'])])
        players = [GameStatePlayer._test_gsplayer("foo", 200, dict([('American', 3), ('Festival', 5)]), set())]

        player = OrderedPlayer('foo')
        keeps = player.keep(GameState._game_state_in_progress(players, board), [A])
        self.assertEquals(keeps, [False])

        keeps = player.keep(GameState._game_state_in_progress(players, board), [A, F])
        self.assertEquals(keeps, [False, False])





if __name__ == '__main__':
    ut.main()
