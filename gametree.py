from copy import deepcopy, copy
from basics import *

from itertools import chain, combinations, product, imap


################################################################################
#### Game Tree Diagram (for the Administrator) #################################
################################################################################
#             +---------------------------------------+
#             |                                       |
#   +-------->|             GameTree                  |
#   |         |                                       |
#   |         +------+---------------------------+----+
#   |                |                           |
#   |                v                           |
#   |  +--------------------------+              |
#   |  | get_tile_moves - [(t,h)] |              +-------------------------+
#   |  +---+----------------------+                                        |
#   |      |            / |  \   choose one, hand to get_sellbacks         |
#   |      |              v                      and get_share_moves       |
#   |      |     +---------------------------+                             |
#   |      |     | get_sellbacks - [{p=>[h]}]|                             |
#   |      |     +-------------+-------------+                             |
#   |      |                /  | \   choose one, hand to get_share_moves   |
#   |      |                   v                                           |
#   |      |             +---------------------------+                     v
#   |      +------------>| get_share_moves - [[h]]   |          +---------------------+
#   |                    +-----------------|---------+          | get_next_tiles - [t]|
#   |                                     /| \  choose one,     +----------+----------+
#   |                                   /  |   \    hand to apply      /   |   \--. choose one, hand to apply
#   |                                 /    |    v                          v       \
#   |                                          +------------------------------+
#   +------------------------------------------+ apply - GameTree             |
#                                              +------------------------------+
# This graph indications the functional flow of dependancies in a
# GameTree.  the methods in small boxes rely on information returned
# from the methods pointing into them.
#
# Proper use of this GameTree will build up information in the order
# presented here to determine all possible valid moves, prune them,
# and then pass a valid move to apply to get a possible next
# state. This next state can be used to create
# a new GameTree recursively.
#
# t = Tile, h = Hotel, p = PlayerName
#
################################################################################
################################################################################


class GameTree:
    """ This class represents a node in an Acquire game tree. Contains methods to
    find possible moves and use them to move to other nodes in the tree.

    """
    def __init__(self, game_state):
        self.game_state = game_state

    def get_tile_moves(self):
        """
        Return all the legal tile placements this player can make

        Return:
            (tile, hotel)

        """
        return [(tile, hotel) for tile in self.game_state.current_player.tiles
                              for hotel in hotels+[None]
                                if self.game_state.is_valid_move(tile, hotel)]

    def get_sellbacks(self, tile, hotel):
        """
        Return all of the potential hotel sellbacks players might want
        to make for a given tile and hotel placement. This only occurs during
        mergers.

        Arguments:
            tile, hotel - a tile move
        Returns:
            if placing tile, hotel would be a merger:
                [{playername=>[sellback_hotels]}] TODO: specify this is a generator <3
            else:
                [{}]
        """
        if self.game_state.board.valid_merge_placement(tile, hotel):
            acquirees = self.game_state.board.acquirees(tile, hotel)

            all_sellbacks = \
                map(list,
                    chain(*[combinations(acquirees, c) for c in range(len(acquirees)+1)]))
            names = [p.name for p in self.game_state.players]

            return imap(dict, product(*(product([n], all_sellbacks) for n in names)))
        else:
            return [{}]

    def get_share_moves(self, tile, hotel, sellback_map):
        """
        Place the tile and hotel on a newly copied instance of this GameTree's
        GameState.

        Arguments:
            tile - tile to place
            hotel - hotel, if necessary, to place assist in the placement, or None.
            sellback_map -  if nessesary, which hotels are boughtback in a merge
                {playername=>[sellback_hotels]} representing which shares should be sold back
        Returns:
            [[hotel]] - where [hotel] is a share move (in ALL_LEGAL_BUYS)

        Note: Will throw GameStateErrors on invalid input (don't do it)
        """
        midturn_gs = deepcopy(self.game_state)
        midturn_gs.place_a_tile(tile, hotel)
        map(lambda player: midturn_gs.sellback(player, sellback_map[player], self.game_state),
            sellback_map.keys())

        return [buy for buy in ALL_LEGAL_BUYS if midturn_gs.is_valid_buy(buy)]

    def get_next_tiles(self):
        """
        Return all the potential tiles that could be given to the current player
        at the end of their turn

        Returns:
            [tile]

        """
        return copy(self.game_state.tile_deck)

    real_id = lambda x: x

    def playable_moves(self,
            tile_moves_filter=real_id,
            sellback_filter=real_id,
            share_moves_filter=real_id,
            next_tiles_filter=real_id,
            return_applied=False):
        """
        Return all possible next moves in a game
        if tile_moves, share_moves or next_tiles are passed in
        restrict moves to ones containing the tiles/shares/next_tiles
        contained in those objects

        Arguments:
            tile_moves_filter - a function that returns a list of tile moves given a list of tile moves
            sellback_filter - a function that returns a list of sellbacks given a list of sellbacks
            share_moves_filter - a function that returns a list of share moves given a list of share moves
            next_tiles_filter - a function that returns a list of tiles given the list of tiles
            return_applied - whether or not we return GameTree objects or a move tuple (see below)

            CONTRACT: A *_filter must take a list and return a subset of its input

            if any or these arguments are not passed in
            all possible legal options will be returned

        Returns:
            if return_applied:
                GameTree representing a potential next move # TODO: specify this is an iterator
            else:
                a move tuple:
                (tile, maybeHotel, shares, next_tile) # TODO: specify this is an iterator
        """
        for tile, maybeHotel in tile_moves_filter(self.get_tile_moves()):
            for sellback in sellback_filter(self.get_sellbacks(tile, maybeHotel)):
                for shares in share_moves_filter(self.get_share_moves(tile, maybeHotel, sellback)):
                    for next_tile in next_tiles_filter(self.get_next_tiles()):
                        if return_applied:
                            yield self.apply(tile, maybeHotel, sellback, shares, next_tile)
                        else:
                            yield tile, maybeHotel, sellback, shares, next_tile

    __iter__ = playable_moves

    def apply(self, tile, maybeHotel, sellbacks, shares, new_tile=None):
        """
        Applies the given move to a game, and returns the new gametree

        Arguments:
            tile - a tile to be placed in this move
            maybeHotel - the hotel used in the time placement or None
            sellbacks - {playername=>[sellback_hotels]} all of the hotels each
                player wants to sell back
            shares - a list of shares to be bought
            new_tile - the tile to be handed out to the player at the end
                of their turn

        Returns:
            A GameTree with the state of the game after this apply
        """
        new_gs = deepcopy(self.game_state)

        new_gs.place_a_tile(tile, maybeHotel)

        for playername in sellbacks:
            new_gs.sellback(playername, sellbacks[playername], self.game_state)

        for share in shares:
            new_gs.buy_stock(share)

        new_gs.merge_payout(tile, maybeHotel, self.game_state)

        new_gs.done(new_tile)

        return GameTree(new_gs)

    ###########################################################################
    #### Faster validity checking methods #####################################
    ###########################################################################
    def is_valid_sell_back(self, tile, hotel, sell_back):
        if not self.game_state.board.valid_merge_placement(tile, hotel):
            return sell_back == {}

        acquirees = self.game_state.board.acquirees(tile, hotel)

        if not set(sell_back.keys()) == set([p.name for p in self.game_state.players]):
            return False

        # all sell_backs are subsets of acquirees
        return all([all([h in acquirees for h in hotels]) for hotels in sell_back.values()])


import unittest as ut
from board  import Board
from state  import GameState, GameStatePlayer
class TestGameTree(ut.TestCase):

    def test_apply(self):
        gt = GameTree(GameState("abc"))
        tile, hotel, keeps, stocks, next_tile = gt.playable_moves().next()

        gt2 = gt.apply(tile, hotel, keeps, stocks, next_tile)
        self.assertEqual(len(gt2.game_state.board.board), 1)

        tile, hotel, keeps, stocks, next_tile = gt2.playable_moves().next()

        gt3 = gt2.apply(tile, hotel, keeps, stocks, next_tile)
        self.assertEqual(len(gt3.game_state.board.board), 2)

    def test_get_tiles_moves(self):
        gt = GameTree(GameState("abc"))
        tile_moves = gt.get_tile_moves()
        self.assertEquals(len(list(tile_moves)), 6)

        for tile, hotel in tile_moves:
            self.assertTrue(gt.game_state.is_valid_move(tile, hotel))

    def test_get_share_moves(self):
        gt = GameTree(GameState("abc"))
        tile, hotel = gt.get_tile_moves()[0]
        share_moves = gt.get_share_moves(tile, hotel, {})
        self.assertEquals(len(list(share_moves)), 11)
        # 11 = (5 stocks available at start * 2) + buying nothing

        for shares in share_moves:
            self.assertTrue(gt.game_state.is_valid_buy(shares))

    def test_get_tile_moves(self):
        gt = GameTree(GameState("abc"))
        next_tiles = gt.get_tile_moves()
        self.assertEquals(len(list(next_tiles)), 6)

    def test_playable_moves(self):
        gt = GameTree(GameState("abc"))

        self.assertEquals(len(list(gt.playable_moves())), 5940)
        # 5940 = 6 * 11 * 90

    def test_get_sellbacks_merge(self):
        player1 = GameStatePlayer._test_gsplayer("joe", 6000, {A:5}, [t5A])
        player2 = GameStatePlayer._test_gsplayer("obama", 6000, {S:4}, [])
        player3 = GameStatePlayer._test_gsplayer("kerry", 6000, {W:4}, [])
        player4 = GameStatePlayer._test_gsplayer("romney", 6000, {W:4}, [])
        player5 = GameStatePlayer._test_gsplayer("ryan", 6000, {W:4}, [])
        player6 = GameStatePlayer._test_gsplayer("mumblesmenino", 6000, {W:4}, [])
        board = Board._board_in_play([(A, [t4A, t3A]), (S, [t6A, t7A]), (W, [t5B, t5C])])
        gt = GameTree(GameState._game_state_in_progress([player1, player2, player3, player4, player5, player6], board))

        self.assertEqual(len(list(gt.get_sellbacks(t5A, A))), (2**2)**6)
    def test_get_sellbacks_no_merge(self):
        gt = GameTree(GameState._game_state_in_progress([GameStatePlayer._test_gsplayer("joe", 6000, {A:5}, [t5A])],
                                                         Board()))
        self.assertEqual(gt.get_sellbacks(t5A, None), [{}])

if __name__ == '__main__':
    ut.main()
