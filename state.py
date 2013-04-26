from random import shuffle
from collections import deque
from copy import copy, deepcopy
from Lib.errors import GameStateError
from basics import *
from board import Board
from Lib.decontractors import Precondition, Postcondition


class GameStatePlayer:

    """ container class for Acquire players """
    def __init__(self):
        self.name = None  # string
        self.money = None  # number
        self.shares_map = None  # dict
        self.tiles = None  # set

    def __eq__(self, other):
        if isinstance(other, GameStatePlayer):
            return self.name == other.name and \
                   self.money == other.money and \
                   self.shares_map == other.shares_map and \
                   self.tiles == other.tiles
        else:
            return False

    def __hash__(self):
        return hash(self.name) ^ \
               hash(self.money) ^ \
               hash(frozenset(self.shares_map.items())) ^ \
               hash(frozenset(self.tiles))


    def __copy__(self):
        player = GameStatePlayer()
        player.name = self.name
        player.money = self.money
        player.shares_map = copy(self.shares_map)
        player.tiles = copy(self.tiles)
        return player

    def __deepcopy__(self, _):
        return self.__copy__()

    @staticmethod
    def _test_gsplayer(name, money, shares_map, tiles):
        """ Build a test player. """
        player = GameStatePlayer()
        player.name = name
        player.money = money
        player.shares_map = shares_map
        player.tiles = tiles
        return player

    def __str__(self):
        return "name: {0}, money: {1}, \
        shares: {2}, tiles: {3}".format(self.name,
                                        self.money,
                                        self.shares_map,
                                        self.tiles)
    __repr__ = __str__

    @Precondition(lambda: hotel in hotels, globals=globals())
    def has_shares_of(self, hotel):
        """ returns whether this player has shares of given hotel """
        return self.shares_map[hotel] > 0

    @Precondition(lambda: hotel in hotels, globals=globals())
    def add_shares(self, hotel, count):
        """ adds count number of shares to this player's number of shares """
        self.shares_map[hotel] += count

    def remove_all_shares(self, hotel):
        """ removes all hotel shares from this player """
        self.shares_map[hotel] = 0


class GameState:

    """ represents a state in an Acquire Game """

    def __init__(self, player_names, handout=lambda x: x[-1], fake_init=False):
        """ starts a new game of acquire and does all necessary setup.

        arguments:
            player_names - array of player names, the game will create a new GameStatePlayer for each name
                            the order they are given in is the turn order
        keyword arguments:
            handout - the strategy with which we will hand tiles out. Default
            is last tile in deque.
            fake_init - will create an uninitialized state for copying
            /
        """
        if fake_init:
            return

        self.board = Board()

        self.tile_deck = copy(coords)
        self.tile_deck.sort(key=tile_sortkey, reverse=True)

        self.players = deque([])
        for name in player_names:
            player = GameStatePlayer()
            self.players.append(player)
            player.name = name
            player.money = STARTING_MONEY
            player.shares_map = dict([(h, 0) for h in hotels])
            player.tiles = set([])
            [self._give_player_tile(player, handout(self.tile_deck)) for _ in xrange(6)]

        self.shares_map = dict([(h, INITIAL_SHARES_PER_HOTEL) for h in hotels])

    def __eq__(self, other):
        if isinstance(other, GameState):
            return set(self.players) == set(other.players) and \
                   self.tile_deck == other.tile_deck and \
                   self.shares_map == other.shares_map and \
                   self.board == other.board
        else:
            return False


    def __copy__(self):
        new_state = GameState([], fake_init=True)
        new_state.board = copy(self.board)
        new_state.tile_deck = copy(self.tile_deck)
        new_state.players = deque([copy(p) for p in self.players])
        new_state.shares_map = copy(self.shares_map)
        return new_state

    def printgs(self):
        """ print this state in a somewhat human readable way """
        # TODO: make this pretty
        print '-=-'*20
        print "Board:", self.board
        print "Deck:", self.tile_deck
        print "Shares:", self.shares_map
        print "Players:"
        for player in self.players:
            print '\tName:', player.name
            print '\tMoney:', player.money
            print '\tTiles:', player.tiles
            print '\tShares:', player.shares_map
        print '-=-'*20

    def __deepcopy__(self, _):
        return self.__copy__()

    @staticmethod
    def _game_state_in_progress(players, board):
        """ create a representation of a game state in progress for tests """
        state = GameState([], False)
        state.players = players
        state.board = board

        used_tiles = set([])
        for player in state.players:
            for tile in player.tiles:
                if tile in used_tiles:
                    raise GameStateError("same tile can only be dealt once: "
                                         + str(tile))
                used_tiles.add(tile)

        for tile in board.board:
            if not board.is_space_free(tile):
                if tile in used_tiles:
                    raise GameStateError("tile in play is currently assigned \
                                         to a player: " + str(tile))
                used_tiles.add(tile)

        for tile in used_tiles:
            state.tile_deck.remove(tile)

        used_shares = dict([(h, 0) for h in hotels])
        for player in state.players:
            for hotel, shares in player.shares_map.items():
                used_shares[hotel] += shares

        for hotel in hotels:
            state.shares_map[hotel] -= used_shares[hotel]
            if state.shares_map[hotel] < 0:
                raise GameStateError("too many shares have been allocated \
                                     in this game state")

        return state

    #########################################################################
    # GameState Properties: #################################################
    #########################################################################
    @property
    @Postcondition(lambda: isinstance(__return__, GameStatePlayer) and self.players[0]==__return__, globals=globals())
    def current_player(self):
        """ returns this game's current player """
        return self.players[0]

    #########################################################################
    # GameState Queries: ####################################################
    #########################################################################
    @Precondition(lambda: isinstance(name, str) and any(p.name==name for p in self.players))
    @Postcondition(lambda: isinstance(__return__, GameStatePlayer), globals=globals())
    def player_with_name(self, name):
        """ Get the player in this game with the given name """
        return [p for p in self.players if p.name == name][0]

    @Precondition(lambda: hotel in hotels, globals=globals())
    @Postcondition(lambda: all(p in self.players and p.shares_map>0 and p.shares_map[hotel]==s for p, s in __return__))
    def players_with_stocks(self, hotel):
        """
        Returns a [(player, share_count)] for  players in this game
        with stocks in the given hotel to the number of stocks they have
        in that hotel

        """
        return [(p, p.shares_map[hotel])
                for p in self.players if p.has_shares_of(hotel)]

    @Precondition(lambda: hotel in hotels, globals=globals())
    @Postcondition(lambda: isinstance(__return__, set)
        and all(all(p.shares_map[hotel] >= p2.shares_map[hotel] for p2 in self.players) for p in __return__))
    def majority_stockholders(self, hotel):
        """
        get the set of the players in this game with the most stocks in the
        given hotel

        """
        players_with_stocks = self.players_with_stocks(hotel)
        max_stocks = max([s for p, s in players_with_stocks])
        return set([p for p, s in players_with_stocks if s == max_stocks])

    @Precondition(lambda: hotel in hotels, globals=globals())
    @Postcondition(lambda: isinstance(__return__, set)
        and all(all(p.shares_map[hotel] >= p2.shares_map[hotel]
                    for p2 in self.players if p2 not in self.majority_stockholders(hotel))
                for p in __return__))
    def minority_stockholders(self, hotel):
        """
        returns the set of the players in this game with the second most stocks
        in the hotel

        """
        not_majority_shareholders = \
            [(p, s) for p, s in self.players_with_stocks(hotel)
             if p not in self.majority_stockholders(hotel)]
        if len(not_majority_shareholders) == 0:
            return set([])
        max_stocks = max([s for p, s in not_majority_shareholders])
        return set([p for p, s in not_majority_shareholders if s == max_stocks])

    def final_scores(self):
        """
        Returns the final scores of this game
        Game must be finished

        Returns:
            dict[playerid -> score]
        """
        # since payouts mutate state, leave this state intact and modify this guy
        final_state = deepcopy(self)
        return dict([(p.name, final_state._final_score(p))
                     for p in final_state.players])

    @Postcondition(lambda: isinstance(__return__, int))
    def _final_score(self, player):
        """
        returns the score of this player

        Arguments:
            player - a GameStatePlayer in this game

        Returns:
            integer
            score = players money + the market value of all their stocks
        """

        #payout merger bonus for all hotels
        for hotel in hotels:
            price = self.board.stock_price(hotel)
            if price is not None and self.shares_map[hotel] < INITIAL_SHARES_PER_HOTEL:
                self.payout(hotel, price, self)

        return (player.money +
                sum([self.board.stock_price(share) * player.shares_map[share]
                     for share in player.shares_map
                     if self.board.stock_price(share) is not None]))

    #########################################################################
    # GameState Commands: ###################################################
    #########################################################################
    # TODO: Fix bug in decontractors that breaks on unnamed kw arguments
    # @Precondition(lambda: self.is_valid_move(coord, hotel), globals=globals())
    def place_a_tile(self, coord, hotel=None):
        """
        Places a tile for this game's current player at the given coord
        and updates a player with their new stock if there's a found.

        If not possible, raises a GameStateError.

        Arguments:
            coord - the location to place a tile
            hotel - the hotel to found or the acquirer in the case of a merge
        """
        def _found():
            """
            This gamestate's current player makes a move to found the given
            hotel at the given coord, rewarding them with an appropriate amount
            of shares.

            """
            if hotel in self.board.hotels_in_play:
                raise GameStateError("tried to found a hotel that's \
                                      already in play" + hotel)
            else:
                self.board.found(coord, hotel)
                # TODO: What to do about the ELSE case here?
                # Relevant if players keep shares in acquired hotels
                #
                # currently is no stock is available
                # the founding player recieves nothing
                if self.shares_map[hotel] > FOUND_SHARES:
                    self.current_player.add_shares(hotel, FOUND_SHARES)
                    self.shares_map[hotel] -= FOUND_SHARES

        move_type = self.board.query(coord)

        if SINGLETON == move_type:
            if hotel is not None:
                raise GameStateError('Placing a singleton can not take a hotel')
            self.board.singleton(coord)
        elif FOUND == move_type:
            if hotel is None:
                raise GameStateError('found requires a hotel name')
            _found()
        elif GROW == move_type:
            if hotel is not None:
                raise GameStateError('Placing a grow should not take a hotel')
            self.board.grow(coord)
        elif MERGE == move_type:  # DOES NOTHING FOR THE PAYOUT
            if hotel is None:
                raise GameStateError('merge requires a hotel name')
            self.board.merge(coord, hotel)
        elif INVALID == move_type:
            raise GameStateError("illegal tile placement")

        self.current_player.tiles.remove(coord)

    def sellback(self, name, sell_hotels, initial_state):
        """
        Sell all stocks from given player back to the to the pool for each of
        the given hotels.

        Arguments:
            name - name of the player
            sell_hotels - a list of hotels to sell
            initial_state - a state providing information about hotel costs
        """
        player = self.player_with_name(name)
        for hotel in sell_hotels:
            if player.has_shares_of(hotel):
                hotel_price = initial_state.board.stock_price(hotel)

                # TODO: remove this
                assert hotel_price is not None

                stocks_amount = player.shares_map[hotel]
                player.money += hotel_price * stocks_amount

                self.shares_map[hotel] += stocks_amount
                player.remove_all_shares(hotel)

    @Precondition(lambda: self.is_valid_buy([hotel]), globals=globals())
    def buy_stock(self, hotel):
        """ this game's current player buys a share of stock in the given hotel """
        stock_price = self.board.stock_price(hotel)

        if stock_price is None:
            raise GameStateError("Cannot buy a hotel that is not in play")

        if self.shares_map[hotel] == 0:
            raise GameStateError("{0} has no shares to buy".format(hotel))

        if self.current_player.money < stock_price:
            raise GameStateError("current player can't afford stock for "+hotel)

        self.shares_map[hotel] -= 1
        self.current_player.money -= stock_price
        self.current_player.shares_map[hotel] += 1

    @Precondition(lambda: tile in coords and maybeHotel in hotels+[None], globals=globals())
    def merge_payout(self, tile, maybeHotel, initial_state, end_of_game=False):
        """
        Perform a merger payout if the given tile, hotel constitute a merger.

        Arguments:
            tile, maybeHotel - a tile move
            initial_state - the state from which we can derive information
                about the merge.
        Effects:
            Adds money to players in this state according to merge payout rules
        """
        if not initial_state.board.valid_merge_placement(tile, maybeHotel):
            return

        acquirer = maybeHotel
        acquirees = initial_state.board.acquirees(tile, acquirer)

        for acquiree in acquirees:

            stock_price = initial_state.board.stock_price(acquiree)
            # TODO: Remove this...
            assert stock_price is not None

            self.payout(acquiree, stock_price, initial_state)

    def payout(self, hotel, price, state):
        """
        Payout the merger bonus for the given hotel at the given price

        Arguments:
            hotel - hotel to pay out for
            price - price of the hotel
            state - state to determine the majority/minority stockholders from
        """

        def to_current_player(player):
            """ returns the player from this gamestate with player's name """
            return self.player_with_name(player.name)

        majority_stockholders = \
            [to_current_player(p)
             for p in state.majority_stockholders(hotel)]
        minority_stockholders = \
            [to_current_player(p)
             for p in state.minority_stockholders(hotel)]
        majority_payout = MAJORITY_PAYOUT_SCALE * price
        minority_payout = MINORITY_PAYOUT_SCALE * price

        if len(majority_stockholders) == 1:
            player = majority_stockholders.pop()
            player.money += majority_payout
            if len(minority_stockholders) == 1:
                player = minority_stockholders.pop()
                player.money += minority_payout
            elif len(minority_stockholders) > 1:
                payout = \
                    divide_and_round_integers(minority_payout,
                                              len(minority_stockholders))
                for player in minority_stockholders:
                    player.money += payout
        else:
            payout = \
             divide_and_round_integers(majority_payout + minority_payout,
                                               len(majority_stockholders))
            for player in majority_stockholders:
                player.money += payout

    @Precondition(lambda: self.is_valid_done(tile), globals=globals())
    def done(self, tile):
        """
        end the this game's current player's turn, allocating a tile if possible
        and moving on to the next player

        """
        if len(self.tile_deck) > 0:
            if tile in self.tile_deck:
                self._give_player_tile(self.current_player, tile)
            else:
                raise GameStateError("tile not in deck " + tile)
        else:
            raise GameStateError("tile_deck is empty")

        self.players.rotate(-1)

    @Precondition(lambda: tile in self.tile_deck and player in self.players)
    def _give_player_tile(self, player, tile):
        """ gives the player in this game the tile and removes it from the deck """
        player.tiles.add(tile)
        self.tile_deck.remove(tile)

    #########################################################################
    # GameState Queries: ####################################################
    #########################################################################
    @Precondition(lambda: hotel in hotels or hotel is None, globals=globals())
    @Precondition(lambda: tile in coords, globals=globals())
    def is_valid_move(self, tile, hotel):
        """ returns whether or not the move is valid given this game state """

        if hotel is None and self.board.valid_singleton_placement(tile):
            return True
        elif self.board.valid_found_placement(tile, hotel):
            return True
        elif self.board.valid_merge_placement(tile, hotel):
            return True
        elif hotel is None and self.board.valid_grow_placement(tile):
            return True
        else:
            return False

    @Precondition(lambda: all([hotel in hotels or hotel is None for hotel in shares]), globals=globals())
    def is_valid_buy(self, shares):
        """ returns whether the given buy move is valid """
        cash = self.current_player.money

        if len(shares) > BUYS_PER_TURN:
            return False

        # players may only buy one type of hotel per turn
        if len(shares) > 0:
            if len(set(shares)) > 1:
                return False

        for share in shares:
            # share must be available
            if shares.count(share) > self.shares_map[share]:
                return False

            # player can afford all shares
            cost = self.board.stock_price(share)
            if cost and cost <= cash:
                cash -= cost
            else:
                return False

        return True

    @Precondition(lambda: tile in coords, globals=globals())
    def is_valid_done(self, tile):
        """ returns whether we can we do a done move with the given tile """
        return tile in self.tile_deck


import unittest


class TestGameState(unittest.TestCase):

    """ Unit tests for GameStates"""
    def setUp(self):
        self.gs = GameState(['jim', 'lori', 'matthias'])

    def test_initialization(self):
        gs = self.gs
        self.assertTrue(isinstance(gs.board, Board))
        self.assertEquals(len(gs.players), 3)
        self.assertEquals(len(gs.current_player.tiles), STARTING_TILES)
        self.assertTrue(all([p.money == STARTING_MONEY for p in gs.players]))
        self.assertEquals(sum([stocks for p in gs.players for _, stocks in p.shares_map.items()]), 0)
        self.assertEquals(gs.current_player.tiles, set(['1A', '2A', '3A', '4A', '5A', '6A']))

    #
    # Tests for Properties:
    #
    def test_current_player(self):
        gs = self.gs
        self.assertEquals(gs.current_player.name, 'jim')

    #
    # Tests for Queries:
    #
    def test_players_with_stocks(self):
        pass

    def test_majority_stockholders(self):
        pass

    def test_minority_stockholders(self):
        pass

    #
    # Tests for External Commands:
    #
    def test_done(self):
        self.assertEqual(self.gs.current_player.name, 'jim')
        self.gs.done(self.gs.tile_deck[0])
        self.assertEqual(self.gs.current_player.name, 'lori')
        self.gs.done(self.gs.tile_deck[0])
        self.assertEqual(self.gs.current_player.name, 'matthias')
        self.gs.done(self.gs.tile_deck[0])
        self.assertEqual(self.gs.current_player.name, 'jim')

    def test_place_a_tile(self):
        gs = self.gs
        gs.place_a_tile('1A')
        self.assertEquals(gs.board['1A'], 'NoHotel')
        self.assertEquals(gs.players[0].tiles, set(['2A', '3A', '4A', '5A', '6A']))

        # can't place a tile we don't own!
        self.assertRaises(GameStateError, gs.place_a_tile, '1A')
        # TODO: more tests needed

    def test_bad_singleton_place_a_tile(self):
        gs = self.gs
        self.assertRaises(GameStateError, gs.place_a_tile, '1A', A)

    def test_bad_singleton_place_a_tile_2(self):
        gs = self.gs
        gs.board.singleton('1A')
        self.assertRaises(GameStateError, gs.place_a_tile, '1A')

    def test_bad_found_place_a_tile(self):
        gs = self.gs
        gs.board.singleton('2A')
        self.assertRaises(GameStateError, gs.place_a_tile, '1A')

    def test_bad_found_place_a_tile_full_board(self):
        gs = self.gs
        gs.board = Board._board_in_play([(A, ["1C", "2C"]), (S, ["4D", "4C"]), (W, ["6C", "7C"]),
            (C, ["1I", "2I"]), (A, ["1F", "2F"]), (A, ["10C", "11C"]), (A, ["10E", "11E"])])
        self.assertRaises(GameStateError, gs.place_a_tile, '1A', C)

    def test_buy_stock(self):
        pass

    #
    # Tests for Internal Commands:
    #
    def test_is_valid_move(self):
        # TODO: STOP BEING BAD! WRITE TESTS YOU DORKS!
        pass

    def test_is_valid_buy(self):
        # TODO: SEE ABOVE YOU JERKS
        pass

    #
    # Tests for Internal Commands:
    #
    def test__singleton(self):
        self.assertEquals(self.gs.board['1A'], Empty)
        self.gs.place_a_tile('1A')
        self.assertEquals(self.gs.board['1A'], NoHotel)
        # TODO: test this invariant once we add decorators
        # self.assertRaises(PreconditionError, self.gs._singleton, '2B')

    def test__found(self):
        # TODO: replace with unittests from
        # gs._found('1A', 'Imperial')
        # Traceback (most recent call last):
        #     ...
        # AssertionError
        # Setup
        gs = self.gs
        gs.place_a_tile('1A')

        gs.place_a_tile('2A', 'Imperial')
        self.assertEquals(gs.board['Imperial'], set(['1A', '2A']))
        self.assertEquals(gs.shares_map['Imperial'], INITIAL_SHARES_PER_HOTEL - 1)
        self.assertEquals(gs.current_player.shares_map['Imperial'], 1)

        # this tests trying to found a second chain with the same name
        # gs.done()
        # gs._singleton('6A')
        # gs.done()
        # this should test a PostConditionError
        # gs._found('5A', 'Imperial')
        # Traceback (most recent call last):
        #     ...
        # GameStateError

    def test__grow(self):
        gs = self.gs

        gs.place_a_tile('1A')
        gs.place_a_tile('2A', 'Continental')
        gs.place_a_tile('3A')
        self.assertEquals(gs.board['Continental'], set(['1A', '2A', '3A']))

    def test__merge(self):
        gs = self.gs

        gs.place_a_tile('4A')
        gs.place_a_tile('5A', 'Imperial')
        gs.done(gs.tile_deck[0])
        gs.place_a_tile('7A')
        gs.place_a_tile('8A', 'Worldwide')
        gs.done(gs.tile_deck[0])
        gs.done(gs.tile_deck[0])

        initial_gs = deepcopy(gs)

        # test with 1 majority owner and no minority owners
        gs.place_a_tile('6A', 'Imperial')
        self.assertEquals(gs.board.hotel_size('Imperial'), 5)
        self.assertEquals(gs.players[1].money, STARTING_MONEY)
        # TODO need to payout merge?
        gs.merge_payout('6A', 'Imperial', initial_gs)
        gs.done(gs.tile_deck[0])
        # payout doesn't happen until turn is ended
        self.assertEquals(gs.players[0].money, STARTING_MONEY + 2000)
        self.assertEquals(gs.players[1].money, STARTING_MONEY)
        self.assertEquals(gs.players[2].money, STARTING_MONEY)

    def test_merge_payout_multiple_majority_one_minority(self):
        gs = self.gs
        gs.board = Board._board_in_play([(A,['2A', '3A', '4A', '5A']), (S,['1B', '1C', '2C'])])
        gs.players[0].shares_map[A] = 3
        gs.players[1].shares_map[A] = 3
        gs.players[2].shares_map[A] = 2

        initial_gs = deepcopy(gs)

        # pretend there are 4 american hotels on the board
        gs.merge_payout('1A', 'Sackson', initial_gs)

        self.assertEquals(gs.players[0].money, 11750)
        self.assertEquals(gs.players[1].money, 11750)
        self.assertEquals(gs.players[2].money, STARTING_MONEY)

    def test_merge_payout_single_majority_multiple_minority(self):
        gs = self.gs
        gs.board = Board._board_in_play([(A,['2A', '3A', '4A', '5A']), (S,['1B', '1C', '2C'])])
        gs.players[0].shares_map[A] = 3
        gs.players[1].shares_map[A] = 2
        gs.players[2].shares_map[A] = 2
        initial_gs = deepcopy(gs)

        # pretend there are 4 american hotels on the board
        gs.merge_payout('1A', 'Sackson', initial_gs)

        self.assertEquals(gs.players[0].money, 13000)
        self.assertEquals(gs.players[1].money, 9250)
        self.assertEquals(gs.players[2].money, 9250)
